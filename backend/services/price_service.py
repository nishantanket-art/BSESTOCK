"""
services/price_service.py
Stock price data via yfinance for price-vs-promoter correlation.
"""

import yfinance as yf
from backend.utils.helpers import get_logger

logger = get_logger("price_service")


def fetch_price_data(ticker: str, period: str = "1y") -> dict | None:
    """
    Fetch stock price history from Yahoo Finance.
    Returns dict with dates, prices, and basic stats.
    """
    try:
        # Indian stocks need .NS suffix for NSE
        yf_ticker = f"{ticker}.NS"
        stock = yf.Ticker(yf_ticker)
        hist = stock.history(period=period)

        if hist.empty:
            # Try BSE
            yf_ticker = f"{ticker}.BO"
            stock = yf.Ticker(yf_ticker)
            hist = stock.history(period=period)

        if hist.empty:
            logger.warning(f"No price data for {ticker}")
            return None

        dates = [d.strftime("%Y-%m-%d") for d in hist.index]
        closes = [round(float(p), 2) for p in hist["Close"]]

        current_price = closes[-1] if closes else 0
        high_52w = max(closes) if closes else 0
        low_52w = min(closes) if closes else 0

        # Calculate price change %
        if len(closes) >= 2:
            price_change_1m = round(((closes[-1] - closes[-min(22, len(closes))]) / closes[-min(22, len(closes))]) * 100, 2)
            price_change_6m = round(((closes[-1] - closes[-min(132, len(closes))]) / closes[-min(132, len(closes))]) * 100, 2)
        else:
            price_change_1m = 0
            price_change_6m = 0

        return {
            "ticker": ticker,
            "dates": dates,
            "prices": closes,
            "current_price": current_price,
            "high_52w": high_52w,
            "low_52w": low_52w,
            "price_change_1m": price_change_1m,
            "price_change_6m": price_change_6m,
            "data_points": len(dates),
        }

    except Exception as e:
        logger.error(f"Error fetching price for {ticker}: {e}")
        return None


def compute_price_promoter_correlation(price_data: dict, holdings: list, quarters: list) -> dict | None:
    """
    Compute correlation between price trend and promoter holding changes.
    Returns data formatted for dual-axis chart.
    """
    if not price_data or not holdings or not quarters:
        return None

    try:
        return {
            "price_dates": price_data["dates"],
            "prices": price_data["prices"],
            "holding_quarters": quarters,
            "holdings": holdings,
            "current_price": price_data["current_price"],
            "price_trend": "up" if price_data.get("price_change_6m", 0) > 0 else "down",
            "holding_trend": "down" if len(holdings) >= 2 and holdings[-1] < holdings[-2] else "stable",
        }
    except Exception as e:
        logger.error(f"Correlation computation error: {e}")
        return None
