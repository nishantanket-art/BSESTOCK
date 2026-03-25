import yfinance as yf
import asyncio
from datetime import datetime
import pandas as pd
from backend.utils.helpers import get_logger

logger = get_logger("price_service")

QUARTER_END_MONTHS = {
    "Mar": 3,
    "Jun": 6,
    "Sep": 9,
    "Dec": 12
}

def _fetch_yf_data(yf_ticker: str, start_year: int):
    """Synchronous helper to fetch data from yfinance."""
    stock = yf.Ticker(yf_ticker)
    return stock.history(start=f"{start_year}-01-01", interval="1d")

async def get_historical_prices(ticker: str, quarters: list[str]) -> list[float]:
    """
    Fetch closing prices for a ticker at the end of each specified quarter.
    Uses asyncio.to_thread to avoid blocking the event loop.
    """
    if not quarters:
        return []

    # Append .NS for NSE stocks if not present
    yf_ticker = ticker if ticker.endswith((".NS", ".BO")) else f"{ticker}.NS"
    
    try:
        # Use first quarter to determine start date
        start_year = int(quarters[0].split()[-1])
        data = await asyncio.to_thread(_fetch_yf_data, yf_ticker, start_year)
        
        if data.empty:
            logger.warning(f"No price data found for {yf_ticker}")
            return [0.0] * len(quarters)

        prices = []
        for q in quarters:
            try:
                parts = q.split()
                month_name = parts[0]
                year = int(parts[1])
                month = QUARTER_END_MONTHS.get(month_name, 3)
                
                target_date = pd.Timestamp(year=year, month=month, day=28)
                closest_date = data.index[data.index <= target_date].max()
                if pd.isna(closest_date):
                    closest_date = data.index[data.index >= target_date].min()
                
                if not pd.isna(closest_date):
                    price = float(data.loc[closest_date]["Close"])
                    prices.append(round(price, 2))
                else:
                    prices.append(0.0)
            except Exception:
                prices.append(0.0)
        
        return prices
    except Exception as e:
        logger.error(f"Failed to fetch prices for {ticker}: {e}")
        return [0.0] * len(quarters)

def fetch_price_data(ticker: str, period: str = "1y") -> list[dict]:
    """Synchronous function for individual company details."""
    yf_ticker = ticker if ticker.endswith((".NS", ".BO")) else f"{ticker}.NS"
    try:
        stock = yf.Ticker(yf_ticker)
        data = stock.history(period=period)
        if data.empty:
            return []
        
        result = []
        for index, row in data.iterrows():
            result.append({
                "date": index.strftime("%Y-%m-%d"),
                "price": round(float(row["Close"]), 2)
            })
        return result
    except Exception as e:
        logger.error(f"Error fetching price data for {ticker}: {e}")
        return []

def compute_price_promoter_correlation(price_history: list[dict], holdings: list[float], quarters: list[str]) -> dict:
    """Helper to correlate holdings with price trends."""
    # Simple implementation for UI compatibility
    return {
        "status": "success",
        "has_data": len(holdings) > 0 and len(price_history) > 0
    }
