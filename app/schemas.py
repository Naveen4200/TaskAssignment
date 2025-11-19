from pydantic import BaseModel
from typing import Optional
from datetime import datetime
# from enum import Enum
from .models import TaskType, TaskFrequency


# class TaskType(str, Enum):
#     IMMEDIATE = "immediate"
#     CUSTOM = "custom"
#
#
# class TaskFrequency(str, Enum):
#     ONE_TIME = "one_time"
#     REPEATED = "repeated"


# Existing schemas...
class LoginSchema(BaseModel):
    username: str
    password: str


class UserCreateSchema(BaseModel):
    username: str
    password: str
    phone_number: str
    is_admin: Optional[bool] = False


class UserResponseSchema(BaseModel):
    id: int
    username: str
    phone_number: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenSchema(BaseModel):
    access_token: str
    token_type: str
    user_type: str


class TokenDataSchema(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    is_admin: Optional[bool] = None


# New Task Schemas
class TaskCreateSchema(BaseModel):
    title: str
    description: str
    assigned_to: int
    task_type: TaskType
    frequency: TaskFrequency
    scheduled_date: Optional[datetime] = None


class TaskResponseSchema(BaseModel):
    id: int
    title: str
    description: str
    assigned_to: int
    created_by: int
    task_type: TaskType
    frequency: TaskFrequency
    scheduled_date: Optional[datetime]
    is_completed: bool
    completed_at: Optional[datetime]
    completion_message: Optional[str]
    completion_image: Optional[str]
    created_at: datetime

    # User details for response
    assigned_user: Optional[UserResponseSchema] = None
    admin_user: Optional[UserResponseSchema] = None

    class Config:
        from_attributes = True


class TaskCompletionSchema(BaseModel):
    completion_message: Optional[str] = None
    # Image will be handled via file upload separately