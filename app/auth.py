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
from .dependencies import get_current_user, admin_required

router = APIRouter(prefix="/auth", tags=["authentication"])


# Default admin creation (run once)
def create_default_admin(db: Session):
    admin_exists = db.query(User).filter(User.username == "admin", User.is_admin == True).first()
    if not admin_exists:
        default_admin = User(
            username="admin",
            phone_number="+1234567890",
            hashed_password=get_password_hash("admin123"),
            is_admin=True
        )
        db.add(default_admin)
        db.commit()
        print("Default admin created: admin/admin123")


@router.post("/login")
async def login_user(
        credentials: LoginSchema,
        db: Session = Depends(get_db)
):
    # Ensure default admin exists
    create_default_admin(db)

    # Fetch user (admin or user)
    user = db.query(User).filter(User.username == credentials.username).first()

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

    # Create JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "is_admin": user.is_admin
        },
        expires_delta=access_token_expires
    )

    return TokenSchema(
        access_token=access_token,
        token_type="bearer",
        user_type="admin" if user.is_admin else "user"
    )


@router.post("/admin/create-user", response_model=UserResponseSchema, operation_id="create_user_admin")
async def create_user(
        user_data: UserCreateSchema,
        current_admin: User = Depends(admin_required),
        db: Session = Depends(get_db)
):
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
        phone_number=user_data.phone_number,
        hashed_password=hashed_password,
        is_admin=user_data.is_admin,
        is_payment_collector=user_data.is_payment_collector
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponseSchema(
        id=new_user.id,
        username=new_user.username,
        phone_number=new_user.phone_number,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        is_payment_collector=new_user.is_payment_collector
    )


@router.get("/me", response_model=UserResponseSchema)
async def get_profile(current_user: User = Depends(get_current_user)):
    return UserResponseSchema(
        id=current_user.id,
        username=current_user.username,
        phone_number=current_user.phone_number,
        is_active=current_user.is_active,
        is_payment_collector=current_user.is_payment_collector,
        created_at=current_user.created_at
    )
