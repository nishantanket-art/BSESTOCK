"""
models/user.py
Pydantic schemas for user authentication.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    display_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    display_name: Optional[str] = None
    created_at: str
    watchlist_count: int = 0


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
