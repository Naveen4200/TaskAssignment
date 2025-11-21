from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from .database import get_db
from .models import User, Task, TaskType, TaskFrequency, RepeatInterval
from .schemas import (
    TaskCreateSchema,
    TaskResponseSchema,
    UserResponseSchema, UserWithStatsSchema, UserStatsResponseSchema
)
from .dependencies import admin_required
from .whatsapp_service import send_whatsapp_message
import requests
import json

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/api-whatsapp")
def api_what():
    url = "https://graph.facebook.com/v19.0/803242889549753/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": "917017419513",
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {"code": "en_US"}
        }
    }

    headers = {
        "Authorization": "Bearer EAATjVTKVX4sBP800DSRIUPxod8ETNK6XaQwzEKQzcmPVX0A6gl1WNIjjxFZCoZCN1fGLBVN7TuXxHpZCN3CTT2WVejhyfMDBybYveDVKVPKLT5egq4EWdee7M7Ho3jza1jrajlXvjFwBJu5jsk6QFNc6VuZAdxVf0RpOHfDn4QKEOChWxQTOwVqwZCrh77i6Vpv8aKinyoxBHf4wtfMwWvUT0YrSZBpuUkmsHpLX2JZAy7aL5ZCyG5oJFgZDZD",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    print(response.status_code)
    print(response.json())


@router.get("/users", response_model=List[UserWithStatsSchema])
async def get_all_users(
        current_admin: User = Depends(admin_required),
        db: Session = Depends(get_db),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        payment_collector: Optional[bool] = Query(None),
        is_active: Optional[bool] = Query(True)
):
    """
    Get all users with statistics (Admin only)
    """
    # Base query
    query = db.query(User).filter(User.is_admin == False)

    # Apply filters
    if payment_collector is not None:
        query = query.filter(User.is_payment_collector == payment_collector)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    users = query.offset(skip).limit(limit).all()

    # Calculate statistics for each user
    users_with_stats = []
    for user in users:
        # Get task statistics
        total_tasks = db.query(Task).filter(Task.assigned_to == user.id).count()
        completed_tasks = db.query(Task).filter(
            Task.assigned_to == user.id,
            Task.is_completed == True
        ).count()
        pending_tasks = total_tasks - completed_tasks

        # Calculate overdue tasks (tasks with due_date that passed and not completed)
        overdue_tasks = db.query(Task).filter(
            Task.assigned_to == user.id,
            Task.is_completed == False,
            Task.due_date < datetime.now(timezone.utc)
        ).count()

        # Calculate completed on time (completed before due_date)
        completed_on_time = db.query(Task).filter(
            Task.assigned_to == user.id,
            Task.is_completed == True,
            Task.completed_at <= Task.due_date
        ).count()

        users_with_stats.append({
            "id": user.id,
            "username": user.username,
            "phone_number": user.phone_number,
            "is_active": user.is_active,
            "is_payment_collector": user.is_payment_collector,
            "created_at": user.created_at,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "overdue_tasks": overdue_tasks,
            "completed_on_time": completed_on_time
        })

    return users_with_stats


@router.post("/tasks", response_model=TaskResponseSchema)
async def create_task(
        task_data: TaskCreateSchema,
        current_admin: User = Depends(admin_required),
        db: Session = Depends(get_db)
):
    """
    Create task with enhanced options (Admin only)
    """
    # Check if assigned user exists and is not admin
    assigned_user = db.query(User).filter(
        User.id == task_data.assigned_to,
        User.is_admin == False
    ).first()

    if not assigned_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or cannot assign tasks to admin"
        )

    # Validate task creation rules
    await validate_task_creation(task_data)

    # Create task
    task = Task(
        title=task_data.title,
        description=task_data.description,
        assigned_to=task_data.assigned_to,
        created_by=current_admin.id,
        task_type=task_data.task_type,
        frequency=task_data.frequency,
        is_payment_task=task_data.is_payment_task,
        due_date=task_data.due_date,
        repeat_interval=task_data.repeat_interval,
        repeat_days=task_data.repeat_days,
        repeat_end_date=task_data.repeat_end_date,
        scheduled_date=task_data.scheduled_date
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    # Handle WhatsApp notification based on task configuration
    await handle_whatsapp_notification(task, assigned_user)

    # Fetch the task with user relationships for response
    task_with_users = db.query(Task).filter(Task.id == task.id).first()
    return task_with_users


async def validate_task_creation(task_data: TaskCreateSchema):
    """Validate task creation rules"""
    current_time = datetime.now(timezone.utc)

    # For ONE_TIME tasks
    if task_data.frequency == TaskFrequency.ONE_TIME:
        if task_data.task_type == TaskType.IMMEDIATE:
            # Immediate one-time task - no due date required, but can have one
            pass
        elif task_data.task_type == TaskType.CUSTOM:
            # Custom one-time task requires scheduled_date
            if not task_data.scheduled_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Scheduled date is required for custom one-time tasks"
                )
            if task_data.scheduled_date <= current_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Scheduled date must be in the future"
                )

    # For REPEATED tasks
    elif task_data.frequency == TaskFrequency.REPEATED:
        if task_data.task_type == TaskType.IMMEDIATE:
            # Immediate repeated task - requires repeat configuration
            if not task_data.repeat_interval:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Repeat interval is required for repeated tasks"
                )
            if task_data.repeat_interval == RepeatInterval.DAYS and not task_data.repeat_days:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Repeat days is required when interval is 'days'"
                )
        elif task_data.task_type == TaskType.CUSTOM:
            # Custom repeated task - requires scheduled_date and repeat configuration
            if not task_data.scheduled_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Scheduled date is required for custom repeated tasks"
                )
            if not task_data.repeat_interval:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Repeat interval is required for repeated tasks"
                )
            if task_data.repeat_interval == RepeatInterval.DAYS and not task_data.repeat_days:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Repeat days is required when interval is 'days'"
                )


async def handle_whatsapp_notification(task: Task, assigned_user: User):
    """Handle WhatsApp notifications based on task configuration"""
    try:
        if task.task_type == TaskType.IMMEDIATE:
            if task.frequency == TaskFrequency.ONE_TIME:
                # Immediate one-time task
                message = f"🚀 *New Immediate Task*\n\n*Title:* {task.title}\n*Description:* {task.description}\n*Due Date:* {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'Not specified'}\n*Priority:* High"
                print(f"📱 [IMMEDIATE ONE-TIME] Sending WhatsApp to {assigned_user.phone_number}: {message}")
                await send_whatsapp_message(assigned_user.phone_number, message)

            else:  # REPEATED
                # Immediate repeated task
                interval_text = get_interval_text(task.repeat_interval, task.repeat_days)
                message = f"🔄 *New Repeated Task*\n\n*Title:* {task.title}\n*Description:* {task.description}\n*Repeat:* {interval_text}\n*Starts:* Immediately"
                print(f"📱 [IMMEDIATE REPEATED] Sending WhatsApp to {assigned_user.phone_number}: {message}")
                await send_whatsapp_message(assigned_user.phone_number, message)

        else:  # CUSTOM
            if task.frequency == TaskFrequency.ONE_TIME:
                # Custom one-time task (scheduled)
                message = f"📅 *Scheduled Task*\n\n*Title:* {task.title}\n*Description:* {task.description}\n*Scheduled for:* {task.scheduled_date.strftime('%Y-%m-%d %H:%M')}\n*Due Date:* {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'Not specified'}"
                print(
                    f"⏰ [SCHEDULED ONE-TIME] Scheduling WhatsApp to {assigned_user.phone_number} at {task.scheduled_date}: {message}")
                await schedule_whatsapp_message(assigned_user.phone_number, message, task.scheduled_date)

            else:  # REPEATED
                # Custom repeated task
                interval_text = get_interval_text(task.repeat_interval, task.repeat_days)
                message = f"📅 *Scheduled Repeated Task*\n\n*Title:* {task.title}\n*Description:* {task.description}\n*Starts:* {task.scheduled_date.strftime('%Y-%m-%d %H:%M')}\n*Repeat:* {interval_text}"
                print(
                    f"⏰ [SCHEDULED REPEATED] Scheduling WhatsApp to {assigned_user.phone_number} starting at {task.scheduled_date}: {message}")
                await schedule_whatsapp_message(assigned_user.phone_number, message, task.scheduled_date)

    except Exception as e:
        print(f"WhatsApp notification failed: {e}")


def get_interval_text(interval: RepeatInterval, days: int = None) -> str:
    """Get human-readable interval text"""
    if interval == RepeatInterval.DAYS:
        return f"Every {days} days"
    elif interval == RepeatInterval.WEEK:
        return "Every week"
    elif interval == RepeatInterval.MONTH:
        return "Every month"
    elif interval == RepeatInterval.YEAR:
        return "Every year"
    return "Unknown"


@router.get("/user-stats/{user_id}", response_model=UserStatsResponseSchema)
async def get_user_statistics(
        user_id: int,
        current_admin: User = Depends(admin_required),
        db: Session = Depends(get_db)
):
    """
    Get detailed statistics for a specific user
    """
    user = db.query(User).filter(User.id == user_id, User.is_admin == False).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Calculate statistics
    total_tasks = db.query(Task).filter(Task.assigned_to == user_id).count()
    completed_tasks = db.query(Task).filter(
        Task.assigned_to == user_id,
        Task.is_completed == True
    ).count()
    pending_tasks = total_tasks - completed_tasks

    overdue_tasks = db.query(Task).filter(
        Task.assigned_to == user_id,
        Task.is_completed == False,
        Task.due_date < datetime.now(timezone.utc)
    ).count()

    completed_on_time = db.query(Task).filter(
        Task.assigned_to == user_id,
        Task.is_completed == True,
        Task.completed_at <= Task.due_date
    ).count()

    return UserStatsResponseSchema(
        user=UserResponseSchema(
            id=user.id,
            username=user.username,
            phone_number=user.phone_number,
            is_active=user.is_active,
            is_payment_collector=user.is_payment_collector,
            created_at=user.created_at
        ),
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        overdue_tasks=overdue_tasks,
        completed_on_time=completed_on_time
    )


@router.get("/tasks", response_model=List[TaskResponseSchema])
async def get_all_tasks(
        current_admin: User = Depends(admin_required),
        db: Session = Depends(get_db),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        completed: Optional[bool] = Query(None),
        task_type: Optional[TaskType] = Query(None)
):
    """
    Get all tasks with user details (Admin only)
    """
    query = db.query(Task)

    # Apply filters if provided
    if completed is not None:
        query = query.filter(Task.is_completed == completed)

    if task_type is not None:
        query = query.filter(Task.task_type == task_type)

    tasks = query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()
    return tasks


@router.get("/tasks/{user_id}", response_model=List[TaskResponseSchema])
async def get_user_tasks(
        user_id: int,
        current_admin: User = Depends(admin_required),
        db: Session = Depends(get_db),
        completed: Optional[bool] = Query(None)
):
    """
    Get specific user's tasks (Admin only)
    """
    # Verify user exists and is not admin
    user = db.query(User).filter(User.id == user_id, User.is_admin == False).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    query = db.query(Task).filter(Task.assigned_to == user_id)

    if completed is not None:
        query = query.filter(Task.is_completed == completed)

    tasks = query.order_by(Task.created_at.desc()).all()
    return tasks


@router.get("/completed-tasks", response_model=List[TaskResponseSchema])
async def get_completed_tasks(
        current_admin: User = Depends(admin_required),
        db: Session = Depends(get_db),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        days: Optional[int] = Query(7, ge=1, description="Number of days to look back")
):
    """
    Get all completed tasks within specified days (Admin only)
    """
    since_date = datetime.now(timezone.utc) - timedelta(days=days)

    tasks = db.query(Task).filter(
        Task.is_completed == True,
        Task.completed_at >= since_date
    ).order_by(Task.completed_at.desc()).offset(skip).limit(limit).all()

    return tasks


@router.get("/tasks-stats")
async def get_task_statistics(
        current_admin: User = Depends(admin_required),
        db: Session = Depends(get_db)
):
    """
    Get task statistics for admin dashboard
    """
    total_tasks = db.query(Task).count()
    completed_tasks = db.query(Task).filter(Task.is_completed == True).count()
    pending_tasks = total_tasks - completed_tasks

    immediate_tasks = db.query(Task).filter(Task.task_type == TaskType.IMMEDIATE).count()
    custom_tasks = db.query(Task).filter(Task.task_type == TaskType.CUSTOM).count()

    one_time_tasks = db.query(Task).filter(Task.frequency == TaskFrequency.ONE_TIME).count()
    repeated_tasks = db.query(Task).filter(Task.frequency == TaskFrequency.REPEATED).count()

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "immediate_tasks": immediate_tasks,
        "custom_tasks": custom_tasks,
        "one_time_tasks": one_time_tasks,
        "repeated_tasks": repeated_tasks
    }


async def schedule_whatsapp_message(phone_number: str, message: str, scheduled_date: datetime):
    """
    Schedule WhatsApp message for custom tasks
    This would integrate with a task scheduler like APScheduler
    """
    print(f"⏰ Scheduling WhatsApp to {phone_number} at {scheduled_date}: {message}")
    # Implementation for scheduling would go here
    return True
