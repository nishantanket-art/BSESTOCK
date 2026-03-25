import sys
import asyncio

# add pr to path
sys.path.append(r"d:\pr")

from backend.database import connect_db, get_db
from backend.routers.scanner import _run_scan_pipeline

async def test():
    print("Connecting to DB...")
    await connect_db()
    db = get_db()
    
    print("Starting scan pipeline...")
    # Override TICKER_UNIVERSE to be small for test
    import backend.services.scraper
    backend.services.scraper.TICKER_UNIVERSE = ["TCS"]
    
    await _run_scan_pipeline()
    
    count = await db.companies.count_documents({})
    print(f"Company count: {count}")
    
    company = await db.companies.find_one({"ticker": "TCS"})
    if company:
        print(f"TCS Found: promoter_change={company.get('promoter_change')}, analysis={bool(company.get('analysis'))}")
    else:
        print("TCS NOT FOUND IN DB")

if __name__ == "__main__":
    asyncio.run(test())
