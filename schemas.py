from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from models import TaskType, TaskFrequency

class LoginSchema(BaseModel):
    username: str
    password: str

class UserCreateSchema(BaseModel):
    username: str
    password: str
    phone_number: str

class TaskCreateSchema(BaseModel):
    title: str
    description: str
    assigned_to: int
    task_type: TaskType
    frequency: TaskFrequency
    scheduled_date: Optional[datetime] = None

class TaskCompletionSchema(BaseModel):
    completion_message: Optional[str] = None
    # For file upload, you'll handle separately

class WhatsAppMessageSchema(BaseModel):
    phone_number: str
    message: str
    task_id: int