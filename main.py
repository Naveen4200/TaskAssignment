# from schemas import LoginSchema, UserCreateSchema, TaskCreateSchema, TaskCompletionSchema, WhatsAppMessageSchema
# from models import User
# from fastapi import Depends
#
# @app.get("/admin/users")
# async def get_all_users(current_admin: User = Depends(get_current_admin)):
#
#
# # Get all users for dropdown
#
# @app.post("/admin/tasks")
# async def create_task(task_data: TaskCreateSchema, current_admin: User = Depends(get_current_admin)):
#
#
# # Create task with all conditions
#
# @app.get("/admin/tasks")
# async def get_all_tasks(current_admin: User = Depends(get_current_admin)):
#
#
# # Get all tasks with user details
#
# @app.get("/admin/tasks/{user_id}")
# async def get_user_tasks(user_id: int, current_admin: User = Depends(get_current_admin)):
#
#
#
#
# @app.get("/admin/completed-tasks")
# async def get_completed_tasks(current_admin: User = Depends(get_current_admin)):
# # Get all completed tasks
#
#
# # user.py
# @app.get("/user/tasks")
# async def get_my_tasks(current_user: User = Depends(get_current_user)):
#
#
# # Get tasks assigned to current user
#
# @app.put("/user/tasks/{task_id}/complete")
# async def mark_task_complete(
#         task_id: int,
#         completion_data: TaskCompletionSchema,
#         current_user: User = Depends(get_current_user)
# ):
#
#
# # auth.py
# @app.post("/admin/login")
# async def admin_login(credentials: LoginSchema):
#
# # Admin login logic
#
# @app.post("/admin/create-user")
# async def create_user(user_data: UserCreateSchema, current_admin: User = Depends(get_current_admin)):
#
# # Create user with username and password
#
# @app.post("/user/login")
# async def user_login(credentials: LoginSchema):
# # User login logic
#
# # whatsapp_service.py
# @app.post("/send-whatsapp")
# async def send_whatsapp_message(message_data: WhatsAppMessageSchema):
#
#
# # Send immediate WhatsApp message
#
# # Background task for scheduled messages
# async def send_scheduled_whatsapp():
# # Check for scheduled tasks and send messages at 9 AM


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth import router as auth_router
from app.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Management System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
