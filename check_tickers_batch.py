import httpx
import asyncio

async def main():
    async with httpx.AsyncClient(follow_redirects=True, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }) as client:
        for ticker in ["ADANIPORTS", "RELIANCE", "TCS", "ZOMATO"]:
            url = f"https://www.screener.in/company/{ticker}/"
            resp = await client.get(url)
            print(f"Ticker: {ticker} | Status: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(main())
