from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from .database import get_db
from .models import User
from .schemas import LoginSchema, UserCreateSchema, UserResponseSchema, TokenSchema
from .auth_utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from .dependencies import get_current_admin
from .dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


# Default admin creation (run once)
def create_default_admin(db: Session):
    admin_exists = db.query(User).filter(User.username == "admin", User.is_admin == True).first()
    if not admin_exists:
        default_admin = User(
            username="admin",
            email="admin@taskmanager.com",
            phone_number="+1234567890",
            hashed_password=get_password_hash("admin123"),
            is_admin=True
        )
        db.add(default_admin)
        db.commit()
        print("Default admin created: admin/admin123")


@router.post("/admin/login")
async def admin_login(
        credentials: LoginSchema,
        db: Session = Depends(get_db)
):
    """
    Admin login endpoint
    """
    # First, check if we need to create default admin
    create_default_admin(db)

    user = db.query(User).filter(
        User.username == credentials.username,
        User.is_admin == True
    ).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "is_admin": True
        },
        expires_delta=access_token_expires
    )

    return TokenSchema(
        access_token=access_token,
        token_type="bearer",
        user_type="admin"
    )


@router.post("/admin/create-user", response_model=UserResponseSchema)
async def create_user(
        user_data: UserCreateSchema,
        current_admin: User = Depends(get_current_admin),
        db: Session = Depends(get_db)
):
    """
    Create a new user (Admin only)
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if phone number already exists
    existing_phone = db.query(User).filter(User.phone_number == user_data.phone_number).first()
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        phone_number=user_data.phone_number,
        hashed_password=hashed_password,
        is_admin=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponseSchema(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        phone_number=new_user.phone_number,
        is_active=new_user.is_active,
        created_at=new_user.created_at
    )


@router.post("/user/login")
async def user_login(
        credentials: LoginSchema,
        db: Session = Depends(get_db)
):
    """
    User login endpoint
    """
    user = db.query(User).filter(
        User.username == credentials.username,
        User.is_admin == False  # Ensure it's not an admin
    ).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "is_admin": False
        },
        expires_delta=access_token_expires
    )

    return TokenSchema(
        access_token=access_token,
        token_type="bearer",
        user_type="user"
    )


@router.get("/admin/me", response_model=UserResponseSchema)
async def get_admin_profile(current_admin: User = Depends(get_current_admin)):
    """
    Get current admin profile
    """
    return UserResponseSchema(
        id=current_admin.id,
        username=current_admin.username,
        email=current_admin.email,
        phone_number=current_admin.phone_number,
        is_active=current_admin.is_active,
        created_at=current_admin.created_at
    )


@router.get("/user/me", response_model=UserResponseSchema)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile
    """
    return UserResponseSchema(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        phone_number=current_user.phone_number,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )
