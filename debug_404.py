import httpx
import asyncio

async def main():
    async with httpx.AsyncClient(follow_redirects=True, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }) as client:
        resp = await client.get("https://www.screener.in/company/ZOMATO/")
        print("Status: ", resp.status_code)
        print("Final URL: ", resp.url)
        print("Headers: ", resp.headers)
        # Check if there is any 'Location' header in the history
        for r in resp.history:
            print(f"Redirect: {r.status_code} -> {r.headers.get('location')}")

if __name__ == "__main__":
    asyncio.run(main())
