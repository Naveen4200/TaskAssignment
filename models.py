from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from enum import Enum
import datetime
from database import Base


class TaskType(str, Enum):
    IMMEDIATE = "immediate"
    CUSTOM = "custom"


class TaskFrequency(str, Enum):
    ONE_TIME = "one_time"
    REPEATED = "repeated"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    phone_number = Column(String, unique=True)  # for WhatsApp
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    task_type = Column(SQLEnum(TaskType))
    frequency = Column(SQLEnum(TaskFrequency))
    scheduled_date = Column(DateTime, nullable=True)  # For custom tasks
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    completion_message = Column(String, nullable=True)
    completion_image = Column(String, nullable=True)  # File path for image
    created_by = Column(Integer, ForeignKey("users.id"))  # Admin who created
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)
    message = Column(String)
    status = Column(String)  # sent, failed