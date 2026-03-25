"""
models/watchlist.py
Pydantic schemas for watchlist operations.
"""

from pydantic import BaseModel
from typing import Optional


class WatchlistAdd(BaseModel):
    ticker: str


class WatchlistItem(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    added_at: str
    promoter_current: Optional[float] = None
    promoter_change: Optional[float] = None
    risk_level: Optional[str] = None
    verdict: Optional[str] = None
