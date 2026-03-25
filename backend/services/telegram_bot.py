"""
services/telegram_bot.py
Send formatted alerts via Telegram Bot API.
"""

import httpx
from backend.config import settings
from backend.utils.helpers import get_logger

logger = get_logger("telegram")

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


async def send_telegram_alert(message: str, chat_id: str = None) -> bool:
    """Send a message via Telegram Bot API."""
    token = settings.TELEGRAM_BOT_TOKEN
    target_chat = chat_id or settings.TELEGRAM_CHAT_ID

    if not token or not target_chat:
        logger.warning("Telegram not configured — skipping alert")
        return False

    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": target_chat,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10.0)
        if resp.status_code == 200:
            logger.info(f"Telegram alert sent to {target_chat}")
            return True
        else:
            logger.error(f"Telegram API error: {resp.status_code} — {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


async def send_scan_alert(results: list[dict]):
    """Send formatted scan results alert."""
    if not results:
        return

    high_risk = [r for r in results if r.get("analysis", {}).get("risk_level") == "High"]
    exits = [r for r in results if r.get("analysis", {}).get("verdict") == "Exit"]

    if not high_risk and not exits:
        return

    lines = ["🚨 <b>Promoter Selling Alert</b>\n"]

    if exits:
        lines.append(f"🔴 <b>{len(exits)} Exit Signal(s):</b>")
        for r in exits[:5]:
            change = r.get("promoter_change", 0)
            lines.append(f"  • {r['ticker']} — holding {r['promoter_current']}% (change: {change}%)")
        lines.append("")

    if high_risk:
        lines.append(f"⚠️ <b>{len(high_risk)} High-Risk:</b>")
        for r in high_risk[:5]:
            change = r.get("promoter_change", 0)
            lines.append(f"  • {r['ticker']} — holding {r['promoter_current']}% (change: {change}%)")

    lines.append(f"\n📊 Total sellers found: {len(results)}")
    await send_telegram_alert("\n".join(lines))
