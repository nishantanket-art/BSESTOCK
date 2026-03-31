"""
routers/stocks.py
Stock listing, company detail, and price correlation endpoints.
"""

import logging
from fastapi import APIRouter, Depends, Query
from typing import Optional

from backend.database import get_db
from backend.services.price_service import fetch_price_data, compute_price_promoter_correlation
from backend.services.news_service import fetch_company_news
from backend.services.analyzer import generate_insights
from backend.utils.auth_utils import get_optional_user
from backend.utils.helpers import safe_float

logger = logging.getLogger("stocks")

router = APIRouter(prefix="/api", tags=["stocks"])


@router.get("/stocks")
async def list_stocks(
    risk: Optional[str] = Query(None, description="Filter by risk level: High, Medium, Low"),
    risk_level: Optional[str] = Query(None, description="Alias for risk filter (frontend compat)"),
    verdict: Optional[str] = Query(None, description="Filter by verdict: Buy, Hold, Caution, Exit"),
    search: Optional[str] = Query(None, description="Search by ticker or company name"),
    sort_by: Optional[str] = Query("risk_score", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(200, ge=1, le=500),
    current_user=Depends(get_optional_user),
):
    """List all tracked companies with filters and sorting."""
    db = get_db()

    # Build filter
    query = {}
    # Accept both 'risk' and 'risk_level' params (frontend sends risk_level)
    effective_risk = risk or risk_level
    if effective_risk:
        query["analysis.risk_level"] = effective_risk
    if verdict:
        query["analysis.verdict"] = verdict
    if search:
        query["$or"] = [
            {"ticker": {"$regex": search.upper(), "$options": "i"}},
            {"company_name": {"$regex": search, "$options": "i"}},
        ]

    # Only show companies that have been analyzed (have promoter change data)
    query["promoter_change"] = {"$exists": True}

    # Sort
    sort_dir = -1 if sort_order == "desc" else 1
    sort_field = f"analysis.{sort_by}" if sort_by in ("risk_score", "risk_level") else sort_by

    # Query
    skip = (page - 1) * limit
    cursor = db.companies.find(query).sort(sort_field, sort_dir).skip(skip).limit(limit)
    companies = await cursor.to_list(length=limit)
    total = await db.companies.count_documents(query)

    # Get user watchlist tickers if authenticated
    watchlist_tickers = set()
    if current_user:
        wl_cursor = db.watchlists.find({"user_id": current_user["_id"]}, {"ticker": 1})
        async for item in wl_cursor:
            watchlist_tickers.add(item["ticker"])

    # Format results
    results = []
    for c in companies:
        analysis = c.get("analysis")
        if not analysis:
            # On-the-fly analysis for items missing it
            from backend.services.analyzer import analyze_company
            analysis = analyze_company(c)
        
        # Safe-guard numeric fields to prevent "Pending" strings leaking to frontend
        prom_current = safe_float(c.get("promoter_current"))
        prom_change = c.get("promoter_change")
        prom_change_val = safe_float(prom_change) if prom_change is not None and prom_change != "Pending" else None

        results.append({
            "ticker": c["ticker"],
            "company_name": c.get("company_name", c["ticker"]),
            "market_cap": c.get("market_cap", "N/A"),
            "promoter_current": prom_current,
            "promoter_change": prom_change_val,
            "fii_current": safe_float(c.get("fii_current")),
            "dii_current": safe_float(c.get("dii_current")),
            "public_current": safe_float(c.get("public_current")),
            "last_scanned": c.get("last_scanned"),
            "in_watchlist": c["ticker"] in watchlist_tickers,
            "analysis": analysis,
            # Legacy fields for older UI
            "risk_level": analysis.get("risk_level", "Low"),
            "verdict": analysis.get("verdict", "Hold"),
            "verdict_icon": analysis.get("verdict_icon", "🟡")
        })

    # Generate insights
    all_companies = await db.companies.find({"promoter_change": {"$exists": True}}).to_list(length=500)
    insights_data = []
    for comp in all_companies:
        insights_data.append({
            "ticker": comp["ticker"],
            "promoter_current": comp.get("promoter_current", 0),
            "promoter_change_abs": comp.get("promoter_change_abs", 0),
            "analysis": comp.get("analysis", {}),
        })
    insights = generate_insights(insights_data)

    # Last scan info
    last_scan = await db.scan_logs.find_one(sort=[("started_at", -1)])

    return {
        "count": total,
        "page": page,
        "limit": limit,
        "results": results,
        "insights": insights,
        "last_scan": last_scan["started_at"].isoformat() if last_scan and hasattr(last_scan.get("started_at"), "isoformat") else str(last_scan.get("started_at", "")) if last_scan else None,
    }


@router.get("/company/{ticker}")
async def get_company(ticker: str, current_user=Depends(get_optional_user)):
    """Get detailed company information with analysis, price data, and news."""
    db = get_db()
    ticker = ticker.upper().strip()

    company = await db.companies.find_one({"ticker": ticker})
    if not company:
        return {"found": False, "message": f"No data found for {ticker}. Run a scan first."}

    # Fetch price data (sync operation — run in thread for async compat)
    import asyncio
    price_data = await asyncio.to_thread(fetch_price_data, ticker)

    # Fetch news
    news = await fetch_company_news(
        company.get("company_name", ticker), ticker
    )

    # Compute price-promoter correlation
    correlation = None
    if price_data:
        correlation = compute_price_promoter_correlation(
            price_data,
            company.get("all_holdings", []),
            company.get("quarters", []),
        )

    # Check if in watchlist
    in_watchlist = False
    if current_user:
        wl = await db.watchlists.find_one({"user_id": current_user["_id"], "ticker": ticker})
        in_watchlist = wl is not None

    # Holdings history
    history_cursor = db.holdings_history.find({"ticker": ticker}).sort("scanned_at", -1).limit(20)
    holdings_history = await history_cursor.to_list(length=20)
    for h in holdings_history:
        h["_id"] = str(h["_id"])

    return {
        "found": True,
        "data": {
            "ticker": company["ticker"],
            "company_name": company.get("company_name", ticker),
            "market_cap": company.get("market_cap", "N/A"),
            "exchange": company.get("exchange", "NSE"),
            "url": company.get("url", ""),
            "promoter_current": company.get("promoter_current", 0.0),
            "promoter_prev": company.get("promoter_prev"),
            "promoter_change": company.get("promoter_change"),
            "promoter_change_abs": company.get("promoter_change_abs"),
            "fii_current": company.get("fii_current", 0.0),
            "dii_current": company.get("dii_current", 0.0),
            "public_current": company.get("public_current", 0.0),
            "all_holdings": company.get("all_holdings", []),
            "quarters": company.get("quarters", []),
            "analysis": company.get("analysis", {}),
            "price_data": price_data,
            "correlation": correlation,
            "news": news,
            "holdings_history": holdings_history,
            "last_scanned": company.get("last_scanned"),
            "in_watchlist": in_watchlist,
        },
    }


@router.get("/trend")
async def get_trend_data():
    """Return aggregated trend data for dashboard charts."""
    db = get_db()

    companies = await db.companies.find({"promoter_change": {"$exists": True}}).to_list(length=500)

    risk_dist = {"High": 0, "Medium": 0, "Low": 0}
    verdict_dist = {"Exit": 0, "Caution": 0, "Hold": 0, "Buy": 0}
    holding_data = []

    for c in companies:
        a = c.get("analysis", {})
        risk = a.get("risk_level", "Low")
        verdict = a.get("verdict", "Hold")
        risk_dist[risk] = risk_dist.get(risk, 0) + 1
        verdict_dist[verdict] = verdict_dist.get(verdict, 0) + 1
        holding_data.append({
            "ticker": c["ticker"],
            "company_name": c.get("company_name", c["ticker"]),
            "current": c.get("promoter_current", 0),
            "previous": c.get("promoter_prev", 0),
            "change": c.get("promoter_change", 0),
            "risk_score": a.get("risk_score", 50),
            "all_holdings": c.get("all_holdings", []),
            "quarters": c.get("quarters", []),
        })

    # Scan history
    scan_logs = await db.scan_logs.find().sort("started_at", -1).limit(30).to_list(length=30)
    for sl in scan_logs:
        sl["_id"] = str(sl["_id"])
        if hasattr(sl.get("started_at"), "isoformat"):
            sl["started_at"] = sl["started_at"].isoformat()

    return {
        "risk_distribution": risk_dist,
        "verdict_distribution": verdict_dist,
        "holding_data": holding_data,
        "scan_history": scan_logs,
    }
@router.get("/prices")
async def get_batch_prices(tickers: str = Query(..., description="Comma separated tickers (e.g. RELIANCE,TCS)")):
    """Batch fetch real-time prices for list of tickers."""
    import yfinance as yf
    import asyncio
    
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        return {}
        
    results = {}
    
    def fetch_price(symbol):
        try:
            # Append .NS for Indian stocks if missing
            yf_symbol = symbol if symbol.endswith(".NS") else f"{symbol}.NS"
            t = yf.Ticker(yf_symbol)
            # Use fast_info for performance
            price = t.fast_info.get("last_price")
            if price is None:
                # Fallback to history
                hist = t.history(period="1d")
                if not hist.empty:
                    price = hist["Close"].iloc[-1]
            return symbol, price
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return symbol, None

    # Fetch Prices in parallel using asyncio to run blocking yf calls in thread pool
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, fetch_price, s) for s in ticker_list]
    price_results = await asyncio.gather(*tasks)
    
    for symbol, price in price_results:
        results[symbol] = round(price, 2) if price else None
        
    return results
