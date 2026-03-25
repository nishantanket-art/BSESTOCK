import httpx
import asyncio

async def main():
    async with httpx.AsyncClient(follow_redirects=True, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }) as client:
        print("Fetching ZOMATO HTML...")
        # Try both simplified and original URLs
        resp = await client.get("https://www.screener.in/company/ZOMATO/")
        print("Status: ", resp.status_code)
        with open("zomato.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        print("Written to zomato.html")

if __name__ == "__main__":
    asyncio.run(main())
