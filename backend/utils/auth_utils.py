"""
utils/auth_utils.py
JWT authentication helpers and password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.config import settings
from backend.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, username: str) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """FastAPI dependency: Returns a dummy user to allow anonymous access."""
    # Dummy user for anonymous access
    dummy_user = {
        "_id": "000000000000000000000000",
        "username": "demo_user",
        "display_name": "Demo User",
        "is_active": True
    }
    
    if credentials is None:
        return dummy_user

    payload = decode_token(credentials.credentials)
    if payload is None:
        return dummy_user

    try:
        db = get_db()
        from bson import ObjectId
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if user is None:
            return dummy_user

        user["_id"] = str(user["_id"])
        return user
    except Exception:
        return dummy_user


async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """FastAPI dependency: returns user if authenticated, else dummy user."""
    return await get_current_user(credentials)
