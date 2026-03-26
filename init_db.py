import asyncio
from backend.services.scraper import run_full_scan
from backend.database import connect_db, close_db

async def scout_and_save():
    print("Connecting to database...")
    await connect_db()
    
    print("Running initial scan to populate database...")
    # Limit scan to 5 tickers for speed during initialization
    import backend.services.scraper as scraper
    original_tickers = scraper.TICKER_UNIVERSE
    scraper.TICKER_UNIVERSE = original_tickers[:10] 
    
    try:
        await run_full_scan()
        print("Initial scan complete.")
    except Exception as e:
        print(f"Scan failed: {e}")
    finally:
        print("Saving database state...")
        await close_db()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(scout_and_save())
