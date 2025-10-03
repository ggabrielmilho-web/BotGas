"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from app.database.base import get_db
from app.database.models import User
from app.core.security import (
    verify_password,
    create_token_pair,
    decode_token,
    verify_token_type
)
from app.services.tenant import TenantService
from app.middleware.tenant import get_current_user, get_current_tenant


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# Pydantic Schemas
class RegisterRequest(BaseModel):
    """Registration request schema"""
    company_name: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{10,14}$")
    cnpj: Optional[str] = Field(None, pattern=r"^\d{14}$")


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    email: str
    full_name: Optional[str]
    role: str
    tenant_id: str
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register new tenant and admin user

    Creates a new tenant with trial period and admin user.
    Returns JWT tokens for immediate authentication.
    """
    # Create tenant (also creates admin user)
    tenant = TenantService.create_tenant(
        db=db,
        company_name=data.company_name,
        email=data.email,
        password=data.password,
        phone=data.phone,
        cnpj=data.cnpj,
        trial_days=7
    )

    # Get the created admin user
    admin_user = db.query(User).filter(
        User.tenant_id == tenant.id,
        User.email == data.email
    ).first()

    # Create token pair
    tokens = create_token_pair(
        user_id=str(admin_user.id),
        tenant_id=str(tenant.id),
        role=admin_user.role
    )

    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens

    Validates credentials and returns access/refresh token pair.
    """
    # Find user by email
    user = db.query(User).filter(User.email == data.email).first()

    # Verify user exists and password is correct
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create token pair
    tokens = create_token_pair(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role
    )

    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token

    Validates refresh token and issues new access/refresh token pair.
    """
    # Decode and verify refresh token
    payload = decode_token(data.refresh_token)
    verify_token_type(payload, "refresh")

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify user still exists and is active
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new token pair
    tokens = create_token_pair(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role
    )

    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information

    Returns user profile based on JWT token.
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        tenant_id=str(current_user.tenant_id),
        is_active=current_user.is_active
    )


@router.post("/logout")
async def logout():
    """
    Logout user

    In JWT-based auth, logout is handled client-side by removing tokens.
    This endpoint exists for API consistency.
    """
    return {"message": "Successfully logged out"}
