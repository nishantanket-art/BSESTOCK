"""
routers/auth.py
Authentication endpoints: signup, login, current user.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime, timezone
from bson import ObjectId

from backend.database import get_db
from backend.models.user import UserSignup, UserLogin, UserResponse, TokenResponse
from backend.utils.auth_utils import (
    hash_password, verify_password, create_access_token, get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
async def signup(data: UserSignup):
    db = get_db()

    existing = await db.users.find_one({"username": data.username.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    user_doc = {
        "username": data.username.lower(),
        "password_hash": hash_password(data.password),
        "display_name": data.display_name or data.username,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "telegram_chat_id": None,
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    token = create_access_token(user_id, data.username.lower())

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            username=data.username.lower(),
            display_name=user_doc["display_name"],
            created_at=user_doc["created_at"],
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    db = get_db()

    user = await db.users.find_one({"username": data.username.lower()})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user_id = str(user["_id"])
    token = create_access_token(user_id, user["username"])

    watchlist_count = await db.watchlists.count_documents({"user_id": user_id})

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            username=user["username"],
            display_name=user.get("display_name"),
            created_at=user.get("created_at", ""),
            watchlist_count=watchlist_count,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    db = get_db()
    user_id = current_user["_id"]
    watchlist_count = await db.watchlists.count_documents({"user_id": user_id})

    return UserResponse(
        id=user_id,
        username=current_user["username"],
        display_name=current_user.get("display_name"),
        created_at=current_user.get("created_at", ""),
        watchlist_count=watchlist_count,
    )
