"""
routers/scanner.py
Scanner control endpoints: trigger scan, check status.
"""

import asyncio
from fastapi import APIRouter, Depends

from backend.services.scraper import run_full_scan, get_scan_status
from backend.services.ai_engine import ai_analyze_all
from backend.services.analyzer import generate_insights
from backend.services.risk_scorer import compute_risk_score, get_risk_label
from backend.services.telegram_bot import send_scan_alert
from backend.database import get_db
from backend.utils.auth_utils import get_current_user

router = APIRouter(prefix="/api/scanner", tags=["scanner"])

_scan_task = None


async def _run_scan_pipeline():
    """Full scan pipeline: scrape → analyze → risk score → persist → alert."""
    db = get_db()

    # Step 1: Scrape
    sellers = await run_full_scan()
    if not sellers:
        return

    # Step 2: AI Analysis
    analyzed = await ai_analyze_all(sellers)

    # Step 3: Risk Scoring
    for item in analyzed:
        score = compute_risk_score(item)
        risk_label = get_risk_label(score)
        item["analysis"]["risk_score"] = score
        item["analysis"]["risk_level"] = risk_label["level"]
        item["analysis"]["risk_color"] = risk_label["color"]
        item["analysis"]["risk_icon"] = risk_label["icon"]

    # Step 4: Persist analysis
    for item in analyzed:
        await db.companies.update_one(
            {"ticker": item["ticker"]},
            {"$set": {
                "analysis": item["analysis"],
                "promoter_change": item.get("promoter_change"),
                "promoter_change_abs": item.get("promoter_change_abs"),
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
            "created_at": r["analysis"]["analyzed_at"],
            "user_id": None,
        })

    # Step 6: Telegram alert
    await send_scan_alert(analyzed)


@router.post("/run")
async def trigger_scan(current_user=Depends(get_current_user)):
    """Manually trigger a full scan."""
    global _scan_task

    status = get_scan_status()
    if status["status"] == "running":
        return {"status": "already_running", "message": "Scan already in progress"}

    _scan_task = asyncio.create_task(_run_scan_pipeline())
    return {"status": "started", "message": "Scan started — this takes 2–3 minutes"}


@router.get("/status")
async def scan_status():
    """Get current scan progress."""
    return get_scan_status()
