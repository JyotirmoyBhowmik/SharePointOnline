"""
Authentication endpoint - Login, logout, token refresh
"""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.auth import authenticate_with_ad, create_access_token, create_refresh_token, decode_token
from app.models.user import User, UserRole

router = APIRouter()
security = HTTPBearer()


# Pydantic schemas
class LoginRequest(BaseModel):
    """Login request with username and password"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response with access and refresh tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user with Active Directory and return JWT tokens
    """
    # Authenticate against AD
    user_data = authenticate_with_ad(login_data.username, login_data.password)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user exists in database, create/update if needed
    user = db.query(User).filter(User.email == user_data['email']).first()
    
    if not user:
        # Create new user
        user = User(
            email=user_data['email'],
            name=user_data['name'],
            department=user_data.get('department'),
            role=user_data['role'],
            ad_username=user_data.get('ad_username'),
            ad_distinguished_name=user_data.get('ad_distinguished_name'),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update user details from AD
        user.name = user_data['name']
        user.department = user_data.get('department')
        user.role = user_data['role']
        user.ad_username = user_data.get('ad_username')
        user.ad_distinguished_name = user_data.get('ad_distinguished_name')
        db.commit()
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Create tokens
    token_data = {
        "sub": user.email,
        "user_id": str(user.user_id),
        "role": user.role.value,
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "department": user.department,
        }
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token
    """
    # Decode refresh token
    payload = decode_token(refresh_data.refresh_token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user_email = payload.get("sub")
    user = db.query(User).filter(User.email == user_email).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new tokens
    token_data = {
        "sub": user.email,
        "user_id": str(user.user_id),
        "role": user.role.value,
    }
    
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "department": user.department,
        }
    }


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client should delete tokens)
    
    Note: With JWT, logout is primarily client-side (deleting tokens).
    Server-side token blacklisting can be implemented using Redis for revocation.
    """
    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user_info(user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return {
        "user_id": str(user.user_id),
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "department": user.department,
        "is_active": user.is_active,
    }
