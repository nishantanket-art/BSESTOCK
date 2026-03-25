import sys
sys.path.append(r"d:\pr")
import asyncio
import httpx
from backend.services.scraper import fetch_company_data

async def main():
    try:
        async with httpx.AsyncClient(follow_redirects=True, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }) as client:
            print("Fetching ZOMATO...")
            data = await fetch_company_data("ZOMATO", client)
            print(f"ZOMATO: {data}")
            
            print("Fetching TCS...")
            data = await fetch_company_data("TCS", client)
            print(f"TCS: {data}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
