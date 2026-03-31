"""
services/scraper.py
Scrapes Screener.in for promoter shareholding data.
Migrated from data_fetcher.py with async support and MongoDB persistence.
"""

import httpx
import asyncio
import random
from bs4 import BeautifulSoup
from datetime import datetime

from backend.config import settings
from backend.database import get_db
from backend.utils.helpers import get_logger, safe_float

logger = get_logger("scraper")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.screener.in/",
}

TICKER_UNIVERSE = [
    # Large Caps
    "ADANIPORTS", "ADANIENT", "ADANIGREEN", "ADANIENSOL",
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "BAJFINANCE", "KOTAKBANK", "LT", "AXISBANK",
    "ASIANPAINT", "MARUTI", "SUNPHARMA", "TITAN", "NESTLEIND",
    "ULTRACEMCO", "WIPRO", "ONGC", "NTPC", "POWERGRID",
    "COALINDIA", "SBILIFE", "HDFCLIFE", "DIVISLAB", "DRREDDY",
    "CIPLA", "EICHERMOT", "HEROMOTOCO", "BAJAJFINSV", "TECHM",
    "TATAMOTORS", "TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL",
    "GRASIM", "INDUSINDBK", "BPCL", "IOC", "HPCL",
    "BRITANNIA", "DABUR", "MARICO", "PIDILITIND", "BERGEPAINT",
    # Mid & Growth Caps
    "MUTHOOTFIN", "CHOLAFIN", "LICHSGFIN",
    "ZOMATO", "NYKAA", "PAYTM", "TRENT", "JUBLFOOD",
    "CUMMINSIND", "THERMAX", "BHEL", "SAIL", "NMDC",
    "FORTIS", "MAXHEALTH", "METROPOLIS", "LALPATHLAB",
    "IRCTC", "CONCOR", "APOLLOHOSP", "ABBOTINDIA",
    "TORNTPHARM", "ALKEM", "AUROPHARMA",
    "VOLTAS", "WHIRLPOOL", "HAVELLS", "POLYCAB",
    "PAGEIND", "RAYMOND", "MANYAVAR",
    "PERSISTENT", "LTIM", "COFORGE", "MPHASIS",
    "INDIANB", "FEDERALBNK", "IDFCFIRSTB", "AAVAS", "ANGELONE",
]

# In-memory scan status (shared across async tasks)
scan_status = {
    "status": "idle",
    "progress": 0,
    "total": 0,
    "current_ticker": "",
    "error": None,
    "started_at": None,
}


async def _safe_get(url: str, client: httpx.AsyncClient, retries: int = 3):
    """HTTP GET with retry and backoff."""
    for attempt in range(retries):
        try:
            resp = await client.get(url, timeout=15.0)
            if resp.status_code == 200:
                return resp
            logger.warning(f"HTTP {resp.status_code} for {url}")
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
        await asyncio.sleep(1.5 * (attempt + 1) + random.uniform(0.3, 0.8))
    return None


def _parse_screener_page(html: str, ticker: str) -> dict | None:
    """Parse Screener.in company page for promoter shareholding."""
    soup = BeautifulSoup(html, "html.parser")

    # Company Name
    name_tag = soup.find("h1")
    company_name = name_tag.get_text(strip=True) if name_tag else ticker

    # Market Cap
    market_cap = "N/A"
    for li in soup.select("#top-ratios li"):
        label = li.find("span", class_="name")
        val = li.find("span", class_="value") or li.find("span", class_="number")
        if label and val:
            if "market cap" in label.get_text(strip=True).lower():
                market_cap = val.get_text(strip=True)
                break

    # Promoter Holding Table
    promoter_current = None
    promoter_prev = None
    all_holdings = []
    quarters = []
    found_shareholding_section = False

    # Holding Table Data (Promoter, FII, DII, Public)
    prom_curr, prom_prev = None, None
    fii_curr, dii_curr, pub_curr = 0.0, 0.0, 0.0
    all_holdings, quarters = [], []
    found_shareholding_section = False

    for section in soup.find_all("section"):
        heading = section.find(["h2", "h3"])
        if heading and "shareholding" in heading.get_text(strip=True).lower():
            found_shareholding_section = True
            table = section.find("table")
            if table:
                rows = table.find_all("tr")
                if rows:
                    headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
                    quarters = headers[1:]
                    for row in rows[1:]:
                        cells = row.find_all(["th", "td"])
                        if not cells: continue
                        label = cells[0].get_text(strip=True).lower()
                        vals = [c.get_text(strip=True).replace("%", "").strip() for c in cells[1:]]
                        float_vals = []
                        for v in vals:
                            try:
                                if v in ("", "-", "n/a"): float_vals.append(None)
                                else: float_vals.append(float(v))
                            except ValueError: float_vals.append(None)
                        
                        if "promoter" in label and "pledge" not in label:
                            all_holdings = float_vals
                            clean = [v for v in float_vals if v is not None]
                            if len(clean) >= 2: prom_curr, prom_prev = clean[-1], clean[-2]
                            elif len(clean) == 1: prom_curr = prom_prev = clean[0]
                        elif "fii" in label:
                            clean = [v for v in float_vals if v is not None]
                            if clean: fii_curr = clean[-1]
                        elif "dii" in label:
                            clean = [v for v in float_vals if v is not None]
                            if clean: dii_curr = clean[-1]
                        elif "public" in label:
                            clean = [v for v in float_vals if v is not None]
                            if clean: pub_curr = clean[-1]
            break

    # Final handling for zero-promoter companies (institutions)
    if found_shareholding_section and prom_curr is None:
        prom_curr, prom_prev = 0.0, 0.0
        all_holdings = [0.0] * (len(quarters) if quarters else 1)

    if prom_curr is None:
        return None

    return {
        "ticker": ticker,
        "company_name": company_name,
        "market_cap": market_cap,
        "promoter_current": prom_curr,
        "promoter_prev": prom_prev,
        "fii_current": fii_curr,
        "dii_current": dii_curr,
        "public_current": pub_curr,
        "all_holdings": [h if h is not None else 0.0 for h in all_holdings],
        "quarters": quarters,
        "exchange": "NSE",
        "url": f"https://www.screener.in/company/{ticker}/",
    }


async def fetch_company_data(ticker: str, client: httpx.AsyncClient) -> dict | None:
    """Fetch and parse data for a single company."""
    url = f"https://www.screener.in/company/{ticker}/consolidated/"
    resp = await _safe_get(url, client)
    if resp is None:
        url = f"https://www.screener.in/company/{ticker}/"
        resp = await _safe_get(url, client)
    if resp is None:
        return None
    return _parse_screener_page(resp.text, ticker)





async def run_full_scan():
    """
    Scan all tickers, detect promoter selling, persist to MongoDB.
    Updates scan_status dict for progress tracking.
    """
    global scan_status

    if scan_status["status"] == "running":
        logger.warning("Scan already in progress")
        return

    scan_status.update({
        "status": "running",
        "progress": 0,
        "total": len(TICKER_UNIVERSE),
        "current_ticker": "",
        "error": None,
        "started_at": datetime.utcnow().isoformat(),
    })

    db = get_db()
    results = []
    total = len(TICKER_UNIVERSE)

    try:
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
            # Warm up session
            try:
                await client.get("https://www.screener.in/", timeout=10.0)
            except Exception:
                pass

            for idx, ticker in enumerate(TICKER_UNIVERSE):
                logger.info(f"Scanning [{idx + 1}/{total}] {ticker}")
                scan_status["progress"] = idx + 1
                scan_status["current_ticker"] = ticker

                data = await fetch_company_data(ticker, client)
                if data is None:
                    await asyncio.sleep(0.4 + random.uniform(0.1, 0.3))
                    continue

                current = data["promoter_current"]
                prev = data["promoter_prev"]
                
                # Calculate change
                change = round(current - prev, 2) if prev is not None else 0
                data["promoter_change"] = change
                data["promoter_change_abs"] = abs(change)

                # Persist company to DB with ALL fields including promoter_change
                await db.companies.update_one(
                    {"ticker": ticker},
                    {"$set": {
                        "company_name": data["company_name"],
                        "market_cap": data["market_cap"],
                        "exchange": data["exchange"],
                        "url": data["url"],
                        "promoter_current": current,
                        "promoter_prev": prev,
                        "promoter_change": change,
                        "promoter_change_abs": abs(change),
                        "fii_current": data.get("fii_current", 0.0),
                        "dii_current": data.get("dii_current", 0.0),
                        "public_current": data.get("public_current", 0.0),
                        "all_holdings": data["all_holdings"],
                        "quarters": data["quarters"],
                        "last_scanned": datetime.utcnow().isoformat(),
                    }},
                    upsert=True,
                )

                # Store holdings history
                await db.holdings_history.insert_one({
                    "ticker": ticker,
                    "promoter_current": current,
                    "promoter_prev": prev,
                    "all_holdings": data["all_holdings"],
                    "scanned_at": datetime.utcnow().isoformat(),
                })

                # Add to results list
                results.append(data)

                await asyncio.sleep(settings.SCRAPER_DELAY + random.uniform(0.2, 0.5))

        results.sort(key=lambda x: x["promoter_change"])

        # Log scan
        await db.scan_logs.insert_one({
            "started_at": datetime.utcnow(),
            "completed_at": datetime.utcnow(),
            "total_scanned": total,
            "sellers_found": len(results),
            "high_risk_count": 0,  # Will be updated after analysis
            "tickers": [r["ticker"] for r in results],
        })

        scan_status["status"] = "done"
        logger.info(f"Scan complete: {len(results)} sellers found out of {total} companies")
        return results

    except Exception as e:
        scan_status["status"] = "error"
        scan_status["error"] = str(e)
        logger.error(f"Scan failed: {e}")
        raise


def get_scan_status() -> dict:
    return dict(scan_status)
