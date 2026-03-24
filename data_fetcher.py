"""
data_fetcher.py
Fetches promoter shareholding data from Screener.in.
Filters companies where:
  - Promoter holding > 40%
  - Promoter holding has DECREASED vs previous quarter (they are selling)
"""

import requests
import time
import random
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# ── Popular NSE-listed tickers to scan (large-cap + mid-cap universe)
TICKER_UNIVERSE = [
    # Large Caps
    "ADANIPORTS", "ADANIENT", "ADANIGREEN", "ADANITRANS",
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "BAJFINANCE", "KOTAKBANK", "LT", "AXISBANK",
    "ASIANPAINT", "MARUTI", "SUNPHARMA", "TITAN", "NESTLEIND",
    "ULTRACEMCO", "WIPRO", "ONGC", "NTPC", "POWERGRID",
    "COALINDIA", "SBILIFE", "HDFCLIFE", "DIVISLAB", "DRREDDY",
    "CIPLA", "EICHERMOT", "HEROMOTOCO", "BAJAJFINSV", "TECHM",
    "TATAMOTORS", "TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL",
    "GRASIM", "INDUSINDBK", "BPCL", "IOC", "HPCL",
    "BRITANNIA", "DABUR", "MARICO", "PIDILITIND", "BERGEPAINT",
    # Mid Caps
    "MUTHOOTFIN", "CHOLAFIN", "LICHSGFIN",
    "ZOMATO", "NYKAA", "DMART", "TRENT", "JUBLFOOD",
    "CUMMINSIND", "THERMAX", "BHEL", "SAIL", "NMDC",
    "FORTIS", "MAXHEALTH", "METROPOLIS", "LALPATHLAB",
    "IRCTC", "CONCOR", "APOLLOHOSP", "ABBOTINDIA",
    "TORNTPHARM", "ALKEM", "AUROPHARMA",
    "VOLTAS", "WHIRLPOOL", "HAVELLS", "POLYCAB",
    "PAGEIND", "RAYMOND", "MANYAVAR",
    "PERSISTENT", "LTIM", "COFORGE", "MPHASIS",
    "INDIANB", "FEDERALBNK", "IDFCFIRSTB",
]


def _safe_get(url: str, session: requests.Session, retries: int = 3, delay: float = 1.5):
    """HTTP GET with retry and backoff."""
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code == 200:
                return resp
            logger.warning(f"HTTP {resp.status_code} for {url}")
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed for {url}: {e}")
        time.sleep(delay * (attempt + 1) + random.uniform(0.3, 0.8))
    return None


def fetch_screener_data(ticker: str, session: requests.Session) -> dict | None:
    """
    Scrape Screener.in company page for promoter shareholding data.
    Returns dict with company info or None if unavailable.
    """
    url = f"https://www.screener.in/company/{ticker}/consolidated/"
    resp = _safe_get(url, session)
    if resp is None:
        url = f"https://www.screener.in/company/{ticker}/"
        resp = _safe_get(url, session)
    if resp is None:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # ── Company Name
    name_tag = soup.find("h1")
    company_name = name_tag.get_text(strip=True) if name_tag else ticker

    # ── Market Cap
    market_cap = "N/A"
    for li in soup.select("#top-ratios li"):
        label = li.find("span", class_="name")
        val = li.find("span", class_="value") or li.find("span", class_="number")
        if label and val:
            ltext = label.get_text(strip=True).lower()
            if "market cap" in ltext:
                market_cap = val.get_text(strip=True)
                break

    # ── Promoter Holding Table (shareholding section)
    promoter_current = None
    promoter_prev = None
    all_holdings = []
    quarters = []

    for section in soup.find_all("section"):
        heading = section.find(["h2", "h3"])
        if heading and "shareholding" in heading.get_text(strip=True).lower():
            table = section.find("table")
            if table:
                rows = table.find_all("tr")
                if rows:
                    headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
                    quarters = headers[1:]
                    for row in rows[1:]:
                        cells = row.find_all(["th", "td"])
                        if not cells:
                            continue
                        label = cells[0].get_text(strip=True).lower()
                        if "promoter" in label and "pledge" not in label:
                            vals = [c.get_text(strip=True).replace("%", "").strip() for c in cells[1:]]
                            for v in vals:
                                try:
                                    all_holdings.append(float(v))
                                except ValueError:
                                    all_holdings.append(None)
                            clean = [v for v in all_holdings if v is not None]
                            if len(clean) >= 2:
                                promoter_current = clean[-1]
                                promoter_prev = clean[-2]
                            elif len(clean) == 1:
                                promoter_current = clean[0]
                            break
            break

    if promoter_current is None:
        return None

    return {
        "ticker": ticker,
        "company_name": company_name,
        "market_cap": market_cap,
        "promoter_current": promoter_current,
        "promoter_prev": promoter_prev,
        "all_holdings": [h for h in all_holdings if h is not None],
        "quarters": quarters,
        "exchange": "NSE",
        "url": f"https://www.screener.in/company/{ticker}/",
    }


def get_promoter_sellers(min_holding: float = 40.0, progress_callback=None) -> list[dict]:
    """
    Scan ticker universe, return companies where:
      - promoter_current > min_holding (default 40%)
      - promoter selling (promoter_current < promoter_prev)
    """
    session = requests.Session()
    try:
        session.get("https://www.screener.in/", headers=HEADERS, timeout=10)
    except Exception:
        pass
    session.headers.update(HEADERS)

    results = []
    total = len(TICKER_UNIVERSE)

    for idx, ticker in enumerate(TICKER_UNIVERSE):
        logger.info(f"Scanning [{idx+1}/{total}] {ticker}")
        if progress_callback:
            progress_callback(idx + 1, total, ticker)

        data = fetch_screener_data(ticker, session)
        if data is None:
            time.sleep(0.4 + random.uniform(0.1, 0.3))
            continue

        current = data["promoter_current"]
        prev = data["promoter_prev"]

        if current >= min_holding and prev is not None and current < prev:
            change = round(current - prev, 2)
            data["promoter_change"] = change
            data["promoter_change_abs"] = abs(change)
            results.append(data)

        time.sleep(0.6 + random.uniform(0.2, 0.5))

    results.sort(key=lambda x: x["promoter_change"])
    logger.info(f"Found {len(results)} companies with promoter selling and holding > {min_holding}%")
    return results


if __name__ == "__main__":
    sellers = get_promoter_sellers()
    for s in sellers:
        print(
            f"{s['ticker']:20s} | Holding: {s['promoter_current']}% "
            f"| Change: {s['promoter_change']}% | Name: {s['company_name']}"
        )
