from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


# Enums for task types
class TaskType(str, enum.Enum):
    IMMEDIATE = "immediate"
    CUSTOM = "custom"


class TaskFrequency(str, enum.Enum):
    ONE_TIME = "one_time"
    REPEATED = "repeated"


class RepeatInterval(str, enum.Enum):
    DAYS = "days"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_payment_collector = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    assigned_tasks = relationship("Task", foreign_keys="Task.assigned_to", back_populates="assigned_user")
    created_tasks = relationship("Task", foreign_keys="Task.created_by", back_populates="admin_user")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_type = Column(Enum(TaskType), nullable=False)
    frequency = Column(Enum(TaskFrequency), nullable=False)
    # For one-time tasks
    due_date = Column(DateTime, nullable=True)
    # For repeated tasks
    repeat_interval = Column(Enum(RepeatInterval), nullable=True)  # days, week, month, year
    repeat_days = Column(Integer, nullable=True)  # Number of days for "days" interval
    repeat_end_date = Column(DateTime, nullable=True)  # When to stop repeating
    # For scheduled tasks
    scheduled_date = Column(DateTime, nullable=True)
    # Task status
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    completion_message = Column(Text, nullable=True)
    completion_image = Column(String(500), nullable=True)
    # Payment collector flag
    is_payment_task = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    assigned_user = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tasks")
    admin_user = relationship("User", foreign_keys=[created_by], back_populates="created_tasks")


class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    sent_at = Column(DateTime, default=datetime.now)
    message = Column(Text, nullable=False)
    status = Column(String(50), default="sent")  # sent, failed
    recipient_number = Column(String(20), nullable=False)
