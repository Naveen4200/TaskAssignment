# from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
# from enum import Enum
# import datetime
# from database import Base
#
#
# class TaskType(str, Enum):
#     IMMEDIATE = "immediate"
#     CUSTOM = "custom"
#
#
# class TaskFrequency(str, Enum):
#     ONE_TIME = "one_time"
#     REPEATED = "repeated"
#
#
# class User(Base):
#     __tablename__ = "users"
#
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, unique=True, index=True)
#     hashed_password = Column(String)
#     phone_number = Column(String, unique=True)  # for WhatsApp
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime, default=datetime.datetime.utcnow)
#
#
# class Task(Base):
#     __tablename__ = "tasks"
#
#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String, index=True)
#     description = Column(String)
#     assigned_to = Column(Integer, ForeignKey("users.id"))
#     task_type = Column(SQLEnum(TaskType))
#     frequency = Column(SQLEnum(TaskFrequency))
#     scheduled_date = Column(DateTime, nullable=True)  # For custom tasks
#     is_completed = Column(Boolean, default=False)
#     completed_at = Column(DateTime, nullable=True)
#     completion_message = Column(String, nullable=True)
#     completion_image = Column(String, nullable=True)  # File path for image
#     created_by = Column(Integer, ForeignKey("users.id"))  # Admin who created
#     created_at = Column(DateTime, default=datetime.datetime.utcnow)
#
#
# class TaskHistory(Base):
#     __tablename__ = "task_history"
#
#     id = Column(Integer, primary_key=True, index=True)
#     task_id = Column(Integer, ForeignKey("tasks.id"))
#     sent_at = Column(DateTime, default=datetime.datetime.utcnow)
#     message = Column(String)
#     status = Column(String)  # sent, failed


# from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
# from enum import Enum
# from .database import Base
# from sqlalchemy.orm import relationship
# from datetime import datetime
#
#
# class TaskType(str, Enum):
#     IMMEDIATE = "immediate"
#     CUSTOM = "custom"
#
#
# class TaskFrequency(str, Enum):
#     ONE_TIME = "one_time"
#     REPEATED = "repeated"
#
#
# class Task(Base):
#     __tablename__ = "tasks"
#
#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String(255), index=True)            # FIXED
#     description = Column(String(1000))                 # FIXED
#     assigned_to = Column(Integer, ForeignKey("users.id"))
#     task_type = Column(SQLEnum(TaskType))
#     frequency = Column(SQLEnum(TaskFrequency))
#     scheduled_date = Column(DateTime, nullable=True)
#     is_completed = Column(Boolean, default=False)
#     completed_at = Column(DateTime, nullable=True)
#     completion_message = Column(String(500), nullable=True)   # FIXED
#     completion_image = Column(String(500), nullable=True)     # FIXED
#     created_by = Column(Integer, ForeignKey("users.id"))
#     created_at = Column(DateTime, default=datetime.utcnow)
#
#
# class User(Base):
#     __tablename__ = "users"
#
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String(50), unique=True, index=True, nullable=False)
#     hashed_password = Column(String(255), nullable=False)
#     phone_number = Column(String(20), unique=True, nullable=False)
#     is_active = Column(Boolean, default=True)
#     is_admin = Column(Boolean, default=False)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
#
#     # Relationships
#     assigned_tasks = relationship("Task", foreign_keys="Task.assigned_to", back_populates="user")
#     created_tasks = relationship("Task", foreign_keys="Task.created_by", back_populates="admin")


from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assigned_tasks = relationship("Task", foreign_keys="Task.assigned_to", back_populates="user")
    created_tasks = relationship("Task", foreign_keys="Task.created_by", back_populates="admin")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_type = Column(Enum(TaskType), nullable=False)
    frequency = Column(Enum(TaskFrequency), nullable=False)
    scheduled_date = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    completion_message = Column(Text, nullable=True)
    completion_image = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tasks")
    admin = relationship("User", foreign_keys=[created_by], back_populates="created_tasks")


class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    message = Column(Text, nullable=False)
    status = Column(String(50), default="sent")  # sent, failed
    recipient_number = Column(String(20), nullable=False)
