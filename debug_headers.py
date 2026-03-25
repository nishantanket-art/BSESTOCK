import httpx
import asyncio
import sys
sys.path.append(r"d:\pr")
from backend.services.scraper import HEADERS, fetch_company_data

async def main():
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # Warm up
        await client.get("https://www.screener.in/")
        
        for ticker in ["ADANIPORTS", "TCS", "ZOMATO"]:
            print(f"Testing {ticker}...")
            data = await fetch_company_data(ticker, client)
            if data:
                print(f"  {ticker} SUCCESS: {data['company_name']}")
            else:
                # Check raw URL status
                url = f"https://www.screener.in/company/{ticker}/"
                resp = await client.get(url)
                print(f"  {ticker} RAW STATUS: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(main())
