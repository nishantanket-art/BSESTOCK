"""
routers/alerts.py
Alert listing and Telegram configuration endpoints.
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from bson import ObjectId

from backend.database import get_db
from backend.models.alert import TelegramSetup
from backend.utils.auth_utils import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
async def get_alerts(
    unread_only: bool = Query(False),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user=Depends(get_current_user),
):
    """Get alerts — both global and user-specific."""
    db = get_db()
    user_id = current_user["_id"]

    query = {
        "$or": [
            {"user_id": None},       # Global alerts
            {"user_id": user_id},     # User-specific alerts
        ]
    }
    if unread_only:
        query["is_read"] = False
    if severity:
        query["severity"] = severity

    cursor = db.alerts.find(query).sort("created_at", -1).limit(limit)
    alerts = await cursor.to_list(length=limit)

    results = []
    for a in alerts:
        results.append({
            "id": str(a["_id"]),
            "ticker": a.get("ticker", ""),
            "company_name": a.get("company_name", ""),
            "alert_type": a.get("alert_type", ""),
            "message": a.get("message", ""),
            "severity": a.get("severity", "medium"),
            "is_read": a.get("is_read", False),
            "created_at": a.get("created_at", ""),
        })

    unread_count = await db.alerts.count_documents({
        "$or": [{"user_id": None}, {"user_id": user_id}],
        "is_read": False,
    })

    return {"count": len(results), "unread_count": unread_count, "alerts": results}


@router.put("/{alert_id}/read")
async def mark_alert_read(alert_id: str, current_user=Depends(get_current_user)):
    """Mark an alert as read."""
    db = get_db()
    try:
        await db.alerts.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": {"is_read": True}},
        )
        return {"message": "Alert marked as read"}
    except Exception:
        return {"message": "Alert not found"}, 404


@router.put("/read-all")
async def mark_all_read(current_user=Depends(get_current_user)):
    """Mark all alerts as read."""
    db = get_db()
    user_id = current_user["_id"]
    await db.alerts.update_many(
        {"$or": [{"user_id": None}, {"user_id": user_id}], "is_read": False},
        {"$set": {"is_read": True}},
    )
    return {"message": "All alerts marked as read"}


@router.post("/telegram-setup")
async def setup_telegram(data: TelegramSetup, current_user=Depends(get_current_user)):
    """Configure Telegram chat ID for alert notifications."""
    db = get_db()
    user_id = current_user["_id"]

    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"telegram_chat_id": data.chat_id}},
    )

    return {"message": "Telegram chat ID configured", "chat_id": data.chat_id}
