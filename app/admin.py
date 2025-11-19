from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from .database import get_db
from .models import User, Task, TaskType, TaskFrequency
from .schemas import (
    TaskCreateSchema,
    TaskResponseSchema,
    UserResponseSchema
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


@router.get("/users", response_model=List[UserResponseSchema])
async def get_all_users(
        current_admin: User = Depends(admin_required),
        db: Session = Depends(get_db),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000)
):
    """
    Get all users for dropdown (Admin only)
    """
    users = db.query(User).filter(User.is_admin == False).offset(skip).limit(limit).all()
    return users


@router.post("/tasks", response_model=TaskResponseSchema)
async def create_task(
        task_data: TaskCreateSchema,
        current_admin: User = Depends(admin_required),
        db: Session = Depends(get_db)
):
    # Check if assigned user exists and is not admin
    assigned_user = db.query(User).filter(User.id == task_data.assigned_to, User.is_admin == False).first()

    if not assigned_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or cannot assign tasks to admin"
        )

    # Validate scheduled_date for CUSTOM tasks
    if task_data.task_type == TaskType.CUSTOM and not task_data.scheduled_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled date is required for custom tasks"
        )

    # Validate scheduled_date is in future for CUSTOM tasks
    if (task_data.task_type == TaskType.CUSTOM and
            task_data.scheduled_date and
            task_data.scheduled_date <= datetime.utcnow()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled date must be in the future for custom tasks"
        )

    # Create task
    task = Task(
        title=task_data.title,
        description=task_data.description,
        assigned_to=task_data.assigned_to,
        created_by=current_admin.id,
        task_type=task_data.task_type,
        frequency=task_data.frequency,
        scheduled_date=task_data.scheduled_date
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    # Handle WhatsApp notification based on task type
    try:
        if task_data.task_type == TaskType.IMMEDIATE:
            # Send immediate WhatsApp message
            message = f"🚀 *New Immediate Task*\n\n*Title:* {task_data.title}\n*Description:* {task_data.description}\n*Priority:* High"
            await send_whatsapp_message(assigned_user.phone_number, message, task.id)

        elif task_data.task_type == TaskType.CUSTOM and task_data.scheduled_date:
            # For custom tasks, schedule the message (you'll need a scheduler)
            message = f"📅 *Scheduled Task*\n\n*Title:* {task_data.title}\n*Description:* {task_data.description}\n*Scheduled for:* {task_data.scheduled_date.strftime('%Y-%m-%d %H:%M')}"
            # Here you would schedule the message for the specific date at 9 AM
            await schedule_whatsapp_message(assigned_user.phone_number, message, task.id, task_data.scheduled_date)

    except Exception as e:
        # Log the error but don't fail the task creation
        print(f"WhatsApp notification failed: {e}")

    # Fetch the task with user relationships for response
    task_with_users = db.query(Task).filter(Task.id == task.id).first()
    return task_with_users


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
    since_date = datetime.utcnow() - timedelta(days=days)

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


async def schedule_whatsapp_message(phone_number: str, message: str, task_id: int, scheduled_date: datetime):
    """
    Schedule WhatsApp message for custom tasks
    This would integrate with a task scheduler like APScheduler
    """
    print(f"⏰ Scheduling WhatsApp to {phone_number} at {scheduled_date}: {message}")
    # Implementation for scheduling would go here
    return True
