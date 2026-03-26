"""
routers/watchlist.py
User watchlist management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from backend.database import get_db
from backend.models.watchlist import WatchlistAdd
from backend.utils.auth_utils import get_current_user

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("")
async def get_watchlist(current_user=Depends(get_current_user)):
    """Get the current user's watchlist with enriched company data."""
    db = get_db()
    user_id = current_user["_id"]

    cursor = db.watchlists.find({"user_id": user_id}).sort("added_at", -1)
    watchlist_items = await cursor.to_list(length=200)

    results = []
    for item in watchlist_items:
        ticker = item["ticker"]
        company = await db.companies.find_one({"ticker": ticker})

        analysis = company.get("analysis", {}) if company else {}
        results.append({
            "ticker": ticker,
            "company_name": company.get("company_name", ticker) if company else ticker,
            "added_at": item.get("added_at", ""),
            "promoter_current": company.get("promoter_current") if company else None,
            "promoter_change": company.get("promoter_change") if company else None,
            "risk_level": analysis.get("risk_level"),
            "risk_score": analysis.get("risk_score"),
            "risk_color": analysis.get("risk_color"),
            "verdict": analysis.get("verdict"),
            "verdict_icon": analysis.get("verdict_icon"),
            "verdict_color": analysis.get("verdict_color"),
            "market_cap": company.get("market_cap", "N/A") if company else "N/A",
            "last_scanned": company.get("last_scanned") if company else None,
        })

    return results


@router.post("")
async def add_to_watchlist(data: WatchlistAdd, current_user=Depends(get_current_user)):
    """Add a stock to the user's watchlist."""
    db = get_db()
    user_id = current_user["_id"]
    ticker = data.ticker.upper().strip()

    existing = await db.watchlists.find_one({"user_id": user_id, "ticker": ticker})
    if existing:
        raise HTTPException(status_code=400, detail=f"{ticker} is already in your watchlist")

    await db.watchlists.insert_one({
        "user_id": user_id,
        "ticker": ticker,
        "added_at": datetime.now(timezone.utc).isoformat(),
    })

    return {"message": f"{ticker} added to watchlist", "ticker": ticker}


@router.delete("/{ticker}")
async def remove_from_watchlist(ticker: str, current_user=Depends(get_current_user)):
    """Remove a stock from the user's watchlist."""
    db = get_db()
    user_id = current_user["_id"]
    ticker = ticker.upper().strip()

    result = await db.watchlists.delete_one({"user_id": user_id, "ticker": ticker})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"{ticker} not found in your watchlist")

    return {"message": f"{ticker} removed from watchlist", "ticker": ticker}
