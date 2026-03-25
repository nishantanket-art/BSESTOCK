"""
services/scheduler.py
APScheduler-based background job scheduler for daily scanning.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.services.scraper import run_full_scan
from backend.services.ai_engine import ai_analyze_all
from backend.services.analyzer import generate_insights
from backend.services.risk_scorer import compute_risk_score, get_risk_label
from backend.services.telegram_bot import send_scan_alert
from backend.database import get_db
from backend.utils.helpers import get_logger

logger = get_logger("scheduler")

scheduler = AsyncIOScheduler()


async def daily_scan_job():
    """
    Daily scan job: scrape → analyze → score → alert → persist.
    """
    logger.info("Starting daily scan job...")
    db = get_db()

    try:
        # Step 1: Scrape
        sellers = await run_full_scan()
        if not sellers:
            logger.info("No promoter sellers found today")
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

        # Step 4: Persist analysis results
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

        # Step 5: Generate and store alerts
        high_risk = [r for r in analyzed if r.get("analysis", {}).get("risk_level") == "High"]
        exits = [r for r in analyzed if r.get("analysis", {}).get("verdict") == "Exit"]

        for r in high_risk + exits:
            alert_type = "exit_signal" if r.get("analysis", {}).get("verdict") == "Exit" else "risk_high"
            await db.alerts.insert_one({
                "ticker": r["ticker"],
                "company_name": r.get("company_name", r["ticker"]),
                "alert_type": alert_type,
                "message": f"{r['ticker']}: Promoter holding at {r['promoter_current']}% (change: {r.get('promoter_change', 0)}%)",
                "severity": "high",
                "is_read": False,
                "created_at": r["analysis"]["analyzed_at"],
                "user_id": None,  # Global alert
            })

        # Step 6: Send Telegram alert
        await send_scan_alert(analyzed)

        # Step 7: Generate insights
        insights = generate_insights(analyzed)

        logger.info(f"Daily scan complete: {len(analyzed)} sellers, {len(high_risk)} high-risk, {len(exits)} exit signals")

    except Exception as e:
        logger.error(f"Daily scan job failed: {e}")


def start_scheduler():
    """Start the APScheduler with daily job at 7 PM IST (1:30 PM UTC)."""
    scheduler.add_job(
        daily_scan_job,
        trigger=CronTrigger(hour=13, minute=30),  # 7 PM IST = 1:30 PM UTC
        id="daily_scan",
        name="Daily Promoter Scan",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — daily scan at 7:00 PM IST")


def stop_scheduler():
    """Shutdown scheduler gracefully."""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
