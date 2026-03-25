"""
models/alert.py
Pydantic schemas for alerts.
"""

from pydantic import BaseModel
from typing import Optional


class AlertResponse(BaseModel):
    id: str
    ticker: str
    company_name: Optional[str] = None
    alert_type: str  # "risk_high", "promoter_decrease", "exit_signal"
    message: str
    severity: str = "medium"  # low, medium, high
    is_read: bool = False
    created_at: str


class TelegramSetup(BaseModel):
    chat_id: str
