import httpx
import asyncio

async def main():
    async with httpx.AsyncClient(follow_redirects=True, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }) as client:
        # Check a few more
        for t in ["HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL"]:
            url = f"https://www.screener.in/company/{t}/"
            resp = await client.get(url)
            print(f"{t}: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(main())
