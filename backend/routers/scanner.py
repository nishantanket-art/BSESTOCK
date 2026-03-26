"""
routers/scanner.py
Scanner control endpoints: trigger scan, check status.
"""

import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends

from backend.services.scraper import run_full_scan, get_scan_status, scan_status
from backend.services.ai_engine import ai_analyze_all
from backend.services.analyzer import generate_insights
from backend.services.risk_scorer import compute_risk_score, get_risk_label
from backend.services.telegram_bot import send_scan_alert
from backend.database import get_db
from backend.utils.auth_utils import get_current_user

import yfinance as yf
import pandas as pd

QUARTER_END_MONTHS = {"Mar": 3, "Jun": 6, "Sep": 9, "Dec": 12}

def _fetch_yf_data(yf_ticker: str, start_year: int):
    stock = yf.Ticker(yf_ticker)
    return stock.history(start=f"{start_year}-01-01", interval="1d")

async def get_historical_prices_inlined(ticker: str, quarters: list[str]) -> list[float]:
    if not quarters: return []
    yf_ticker = ticker if ticker.endswith((".NS", ".BO")) else f"{ticker}.NS"
    try:
        start_year = int(quarters[0].split()[-1])
        data = await asyncio.to_thread(_fetch_yf_data, yf_ticker, start_year)
        if data.empty: return [0.0] * len(quarters)
        prices = []
        for q in quarters:
            try:
                parts = q.split(); m_name = parts[0]; yr = int(parts[1])
                target = pd.Timestamp(year=yr, month=QUARTER_END_MONTHS.get(m_name, 3), day=28)
                closest = data.index[data.index <= target].max()
                if pd.isna(closest): closest = data.index[data.index >= target].min()
                prices.append(round(float(data.loc[closest]["Close"]), 2) if not pd.isna(closest) else 0.0)
            except: prices.append(0.0)
        return prices
    except: return [0.0] * len(quarters)

router = APIRouter(prefix="/api/scanner", tags=["scanner"])

_scan_task = None


async def _run_scan_pipeline():
    """Full scan pipeline: scrape → analyze → risk score → persist → alert."""
    from backend.services.scraper import scan_status
    db = get_db()
    
    try:
        # Step 1: Scrape
        sellers = await run_full_scan()
        if not sellers:
            print("[INFO] No sellers found in scan")
            return

        # Step 2: AI Analysis
        analyzed = await ai_analyze_all(sellers)

        # Step 3: Risk Scoring & Price Correlation
        sem = asyncio.Semaphore(5)

        async def enrich_item(item):
            async with sem:
                # Ensure analysis field exists even if AI failed
                if "analysis" not in item:
                    from backend.services.analyzer import analyze_company
                    item["analysis"] = analyze_company(item)
                
                quarters = item.get("quarters", [])
                if quarters:
                    prices = await get_historical_prices_inlined(item["ticker"], quarters)
                    item["all_prices"] = prices
                
                score = compute_risk_score(item)
                risk_label = get_risk_label(score)
                item["analysis"]["risk_score"] = score
                item["analysis"]["risk_level"] = risk_label["level"]
                item["analysis"]["risk_color"] = risk_label["color"]
                item["analysis"]["risk_icon"] = risk_label["icon"]
                return item

        enrich_tasks = [enrich_item(item) for item in analyzed]
        analyzed = await asyncio.gather(*enrich_tasks)

        # Step 4: Persist analysis and prices
        for item in analyzed:
            await db.companies.update_one(
                {"ticker": item["ticker"]},
                {"$set": {
                    "analysis": item["analysis"],
                    "promoter_change": item.get("promoter_change"),
                    "promoter_change_abs": item.get("promoter_change_abs"),
                    "all_prices": item.get("all_prices", []),
                }},
                upsert=True,
            )

        # Step 5: Create alerts for high-risk
        high_risk = [r for r in analyzed if r.get("analysis", {}).get("risk_level") == "High"]
        exits = [r for r in analyzed if r.get("analysis", {}).get("verdict") == "Exit"]

        for r in high_risk + exits:
            alert_type = "exit_signal" if r.get("analysis", {}).get("verdict") == "Exit" else "risk_high"
            await db.alerts.insert_one({
                "ticker": r["ticker"],
                "company_name": r.get("company_name", r["ticker"]),
                "alert_type": alert_type,
                "message": f"{r['ticker']}: Promoter at {r['promoter_current']}% (change: {r.get('promoter_change', 0)}%)",
                "severity": "high",
                "is_read": False,
                "created_at": datetime.utcnow(),
                "user_id": None,
            })

        # Step 6: Telegram alert
        await send_scan_alert(analyzed)
        print("[SUCCESS] Scan pipeline completed")

    except Exception as e:
        print(f"[ERROR] Scan pipeline crashed: {e}")
        import traceback
        traceback.print_exc()
        scan_status["status"] = "error"
        scan_status["error"] = str(e)



@router.post("/run")
async def trigger_scan(current_user=Depends(get_current_user)):
    """Manually trigger a full scan."""
    global _scan_task

    status = get_scan_status()
    if status["status"] == "running":
        return {"status": "already_running", "message": "Scan already in progress"}

    _scan_task = asyncio.create_task(_run_scan_pipeline())
    return {"status": "started", "message": "Scan started — this takes 2–3 minutes"}


@router.post("/reanalyze")
async def trigger_reanalysis(current_user=Depends(get_current_user)):
    """Re-run AI analysis on existing data without scraping."""
    db = get_db()
    
    # Fetch existing companies
    companies = await db.companies.find().to_list(1000)
    if not companies:
        return {"status": "empty", "message": "No companies in database to analyze"}

    # Run AI Analysis & Risk Scoring
    analyzed = await ai_analyze_all(companies)
    for item in analyzed:
        score = compute_risk_score(item)
        risk_label = get_risk_label(score)
        item["analysis"]["risk_score"] = score
        item["analysis"]["risk_level"] = risk_label["level"]
        item["analysis"]["risk_color"] = risk_label["color"]
        item["analysis"]["risk_icon"] = risk_label["icon"]

        await db.companies.update_one(
            {"ticker": item["ticker"]},
            {"$set": {"analysis": item["analysis"]}}
        )

    return {"status": "success", "count": len(analyzed), "message": f"Re-analyzed {len(analyzed)} companies"}


@router.get("/status")
async def scan_status_endpoint():
    """Get current scan progress."""
    return get_scan_status()
