import json
import os
from motor.motor_asyncio import AsyncIOMotorClient
from mongomock_motor import AsyncMongoMockClient
from backend.config import settings

client = None
db = None
STATE_FILE = "db_state.json"


async def load_state():
    """Load companies from JSON state file into mock DB."""
    global db
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                if "companies" in data:
                    for company in data["companies"]:
                        await db.companies.replace_one({"ticker": company["ticker"]}, company, upsert=True)
            print(f"[OK] Restored {len(data.get('companies', []))} companies from {STATE_FILE}")
        except Exception as e:
            print(f"[ERROR] Failed to load state: {e}")


async def save_state():
    """Save companies from mock DB to JSON state file."""
    global db
    try:
        companies = await db.companies.find().to_list(1000)
        with open(STATE_FILE, "w") as f:
            json.dump({"companies": companies}, f, default=str)
        print(f"[OK] Saved {len(companies)} companies to {STATE_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to save state: {e}")


async def connect_db():
    """Initialize MongoDB connection (Persistent or Mock fallback)."""
    global client, db
    
    if settings.MONGODB_URI and "mongodb" in settings.MONGODB_URI and "localhost" not in settings.MONGODB_URI:
        try:
            client = AsyncIOMotorClient(settings.MONGODB_URI)
            await client.admin.command('ping')
            print(f"[OK] Connected to PERSISTENT MongoDB: {settings.DATABASE_NAME}")
        except Exception as e:
            print(f"[WARNING] Persistent DB connection failed: {e}")
            client = AsyncMongoMockClient()
    else:
        print("[INFO] Using mock database with JSON persistence.")
        client = AsyncMongoMockClient()
        
    db = client[settings.DATABASE_NAME]

    # Create indexes
    await db.users.create_index("username", unique=True)
    await db.companies.create_index("ticker", unique=True)
    await db.holdings_history.create_index([("ticker", 1), ("scanned_at", -1)])
    await db.watchlists.create_index([("user_id", 1), ("ticker", 1)], unique=True)
    await db.alerts.create_index([("user_id", 1), ("created_at", -1)])
    await db.scan_logs.create_index("started_at", expireAfterSeconds=2592000)

    # Load state if mock
    if isinstance(client, AsyncMongoMockClient):
        await load_state()

    print(f"[OK] Database initialized: {settings.DATABASE_NAME}")


async def close_db():
    """Close MongoDB connection and save state if mock."""
    global client
    if client:
        if isinstance(client, AsyncMongoMockClient):
            await save_state()
        print("[OK] Closing database connection")


def get_db():
    """Get database instance."""
    return db
