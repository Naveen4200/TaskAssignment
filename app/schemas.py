# from pydantic import BaseModel
# from datetime import datetime
# from typing import Optional
# from models import TaskType, TaskFrequency
#
# class LoginSchema(BaseModel):
#     username: str
#     password: str
#
# class UserCreateSchema(BaseModel):
#     username: str
#     password: str
#     phone_number: str
#
# class TaskCreateSchema(BaseModel):
#     title: str
#     description: str
#     assigned_to: int
#     task_type: TaskType
#     frequency: TaskFrequency
#     scheduled_date: Optional[datetime] = None
#
# class TaskCompletionSchema(BaseModel):
#     completion_message: Optional[str] = None
#     # For file upload, you'll handle separately
#
# class WhatsAppMessageSchema(BaseModel):
#     phone_number: str
#     message: str
#     task_id: int


# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class LoginSchema(BaseModel):
    username: str
    password: str


class UserCreateSchema(BaseModel):
    username: str
    password: str
    phone_number: str
    email: Optional[EmailStr] = None


class UserResponseSchema(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
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