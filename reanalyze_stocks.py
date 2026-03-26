import asyncio
from backend.database import connect_db, get_db
from backend.services.ai_engine import ai_analyze_all
from backend.services.risk_scorer import compute_risk_score, get_risk_label

async def run_reanalysis():
    print("Connecting to database...")
    await connect_db()
    db = get_db()
    
    print("Fetching companies...")
    companies = await db.companies.find().to_list(1000)
    if not companies:
        print("No companies found in database.")
        return
    
    print(f"Found {len(companies)} companies. Starting AI Analysis...")
    analyzed = await ai_analyze_all(companies)
    
    print("Scoring risks and updating database...")
    for item in analyzed:
        score = compute_risk_score(item)
        risk = get_risk_label(score)
        
        # Ensure 'analysis' field exists
        if "analysis" not in item:
            from backend.services.analyzer import analyze_company
            item["analysis"] = analyze_company(item)
            
        item["analysis"]["risk_score"] = score
        item["analysis"]["risk_level"] = risk["level"]
        item["analysis"]["risk_color"] = risk["color"]
        item["analysis"]["risk_icon"] = risk["icon"]
        
        await db.companies.update_one(
            {"ticker": item["ticker"]},
            {"$set": {"analysis": item["analysis"]}}
        )
        print(f" [+] Updated {item['ticker']}: {item['analysis']['verdict']}")

    print("\nRe-analysis complete!")

if __name__ == "__main__":
    asyncio.run(run_reanalysis())
