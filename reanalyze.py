import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from backend.services.analyzer import analyze_company
from backend.config import settings

async def reanalyze_all():
    print("Re-analyzing all companies...")
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]
    
    companies = await db.companies.find().to_list(1000)
    for c in companies:
        ticker = c["ticker"]
        print(f"Analyzing {ticker}...")
        analysis = analyze_company(c)
        await db.companies.update_one(
            {"ticker": ticker},
            {"$set": {"analysis": analysis}}
        )
    print("Finished!")

if __name__ == "__main__":
    asyncio.run(reanalyze_all())
