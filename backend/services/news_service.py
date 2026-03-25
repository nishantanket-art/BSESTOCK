"""
services/news_service.py
Fetch company-related news headlines from Google News RSS.
"""

import httpx
from xml.etree import ElementTree
from backend.utils.helpers import get_logger

logger = get_logger("news_service")

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"


async def fetch_company_news(company_name: str, ticker: str, limit: int = 8) -> list[dict]:
    """
    Fetch recent news articles about a company from Google News RSS.
    """
    try:
        query = f"{company_name} OR {ticker} stock promoter"
        url = GOOGLE_NEWS_RSS.format(query=query.replace(" ", "+"))

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0, headers={
                "User-Agent": "Mozilla/5.0 (compatible; StockMonitor/1.0)"
            })

        if resp.status_code != 200:
            logger.warning(f"News fetch failed with status {resp.status_code}")
            return []

        root = ElementTree.fromstring(resp.text)
        channel = root.find("channel")
        if channel is None:
            return []

        articles = []
        for item in channel.findall("item")[:limit]:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            source = item.findtext("source", "")

            if title:
                articles.append({
                    "title": title,
                    "url": link,
                    "published_at": pub_date,
                    "source": source,
                })

        logger.info(f"Fetched {len(articles)} news articles for {ticker}")
        return articles

    except Exception as e:
        logger.error(f"News fetch error for {ticker}: {e}")
        return []
