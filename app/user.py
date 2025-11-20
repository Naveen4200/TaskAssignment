from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os

from .database import get_db
from .models import User, Task
from .schemas import TaskResponseSchema, TaskCompletionSchema
from .dependencies import get_current_user

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/tasks", response_model=List[TaskResponseSchema])
async def get_my_tasks(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        completed: Optional[bool] = Query(None)
):
    """
    Get tasks assigned to current user
    """
    query = db.query(Task).filter(Task.assigned_to == current_user.id)

    if completed is not None:
        query = query.filter(Task.is_completed == completed)

    tasks = query.order_by(Task.created_at.desc()).all()
    return tasks


@router.put("/tasks/{task_id}/complete")
async def mark_task_complete(
        task_id: int,
        completion_data: TaskCompletionSchema,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Mark task as complete with message
    """
    task = db.query(Task).filter(Task.id == task_id, Task.assigned_to == current_user.id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task already completed"
        )

    task.is_completed = True
    task.completed_at = datetime.now()
    task.completion_message = completion_data.completion_message

    db.commit()
    db.refresh(task)

    return {"message": "Task marked as completed", "task": task}


@router.put("/tasks/{task_id}/complete-with-image")
async def complete_task_with_image(
        task_id: int,
        completion_message: str = Form(None),
        image: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id, Task.assigned_to == current_user.id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task already completed"
        )

    # Create uploads directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)

    # Save image
    file_extension = os.path.splitext(image.filename)[1]
    filename = f"task_{task_id}_{current_user.id}_{datetime.now().timestamp()}{file_extension}"
    file_path = f"uploads/{filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # Update task
    task.is_completed = True
    task.completed_at = datetime.now()
    task.completion_message = completion_message
    task.completion_image = file_path

    db.commit()
    db.refresh(task)

    return {"message": "Task completed with image", "task": task}
