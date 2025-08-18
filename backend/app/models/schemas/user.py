"""
User schemas for BeSunny.ai Python backend.
Defines data models for user authentication and management.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    """User model."""
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    username: Optional[str] = Field(None, description="Username")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class UserCreate(BaseModel):
    """User creation request."""
    email: EmailStr = Field(..., description="User email address")
    username: Optional[str] = Field(None, description="Username")
    password: str = Field(..., description="User password", min_length=8)


class UserUpdate(BaseModel):
    """User update request."""
    username: Optional[str] = Field(None, description="Username")
    email: Optional[EmailStr] = Field(None, description="User email address")


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """User response (without sensitive data)."""
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    username: Optional[str] = Field(None, description="Username")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class Token(BaseModel):
    """Authentication token."""
    access_token: str = Field(..., description="Access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Token data payload."""
    user_id: Optional[str] = Field(None, description="User ID from token")
    email: Optional[str] = Field(None, description="User email from token")
