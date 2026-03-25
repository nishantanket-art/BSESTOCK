import httpx
import asyncio

async def main():
    async with httpx.AsyncClient(follow_redirects=True, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }) as client:
        print("Fetching HTML...")
        resp = await client.get("https://www.screener.in/company/TCS/")
        print("Status: ", resp.status_code)
        with open("test.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        print("Written to test.html")

if __name__ == "__main__":
    asyncio.run(main())
