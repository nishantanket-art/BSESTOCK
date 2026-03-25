"""
models/company.py
Pydantic schemas for company and holdings data.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CompanyBase(BaseModel):
    ticker: str
    company_name: str
    market_cap: Optional[str] = "N/A"
    exchange: str = "NSE"
    sector: Optional[str] = None
    url: Optional[str] = None


class HoldingSnapshot(BaseModel):
    ticker: str
    promoter_current: float
    promoter_prev: Optional[float] = None
    promoter_change: Optional[float] = None
    promoter_change_abs: Optional[float] = None
    all_holdings: List[float] = []
    quarters: List[str] = []
    scanned_at: str


class CompanyAnalysis(BaseModel):
    # Risk
    risk_level: str = "Low"
    risk_score: int = 50  # 0-100
    risk_color: str = "#00cc88"

    # Verdict
    verdict: str = "Hold"
    verdict_color: str = "#ffc107"
    verdict_icon: str = "🟡"
    verdict_desc: str = ""

    # AI Analysis
    ai_reason: Optional[str] = None
    ai_outlook: Optional[str] = None
    ai_explanation: Optional[str] = None

    # Rule-based fallback
    category: str = "small_selloff"
    reasons: List[str] = []
    sentiment: str = "Neutral"
    mode_of_selling: str = ""
    recommendation: str = ""

    # Intent
    intent_confidence: str = "High"
    intent_is_trend: bool = False
    intent_pattern: str = ""

    # Impact
    impact_governance: str = "Neutral"
    impact_perception: str = ""
    impact_short_term: str = ""
    impact_long_term: str = ""

    analyzed_at: str = ""


class CompanyDetail(CompanyBase):
    promoter_current: float = 0
    promoter_prev: Optional[float] = None
    promoter_change: Optional[float] = None
    promoter_change_abs: Optional[float] = None
    all_holdings: List[float] = []
    quarters: List[str] = []
    analysis: Optional[CompanyAnalysis] = None
    price_data: Optional[dict] = None
    news: Optional[List[dict]] = None
    last_scanned: Optional[str] = None


class CompanyListItem(BaseModel):
    ticker: str
    company_name: str
    market_cap: Optional[str] = "N/A"
    promoter_current: float = 0
    promoter_change: Optional[float] = None
    risk_level: str = "Low"
    risk_score: int = 50
    verdict: str = "Hold"
    verdict_icon: str = "🟡"
    last_scanned: Optional[str] = None
    in_watchlist: bool = False


class StockListResponse(BaseModel):
    count: int
    results: List[CompanyListItem]
    insights: List[dict] = []
    last_scan: Optional[str] = None
