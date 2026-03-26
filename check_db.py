import asyncio
from backend.database import connect_db, get_db

async def check():
    await connect_db()
    db = get_db()
    
    # Check one company
    company = await db.companies.find_one({"analysis.verdict": {"$exists": True}})
    if company:
        print(f"Ticker: {company['ticker']}")
        print(f"Verdict: {company['analysis']['verdict']}")
        print(f"Risk: {company['analysis']['risk_level']} ({company['analysis']['risk_score']})")
        print(f"Summary: {company['analysis'].get('summary', 'NO SUMMARY')[:100]}...")
    else:
        print("No analyzed companies found.")

    # Check total count
    count = await db.companies.count_documents({"analysis.verdict": {"$exists": True}})
    print(f"Total analyzed: {count}")

if __name__ == "__main__":
    asyncio.run(check())
