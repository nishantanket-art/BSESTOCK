"""
database.py
MongoDB connection using Motor (async driver).
"""

from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    """Initialize MongoDB connection."""
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]

    # Create indexes
    await db.users.create_index("username", unique=True)
    await db.companies.create_index("ticker", unique=True)
    await db.holdings_history.create_index([("ticker", 1), ("scanned_at", -1)])
    await db.watchlists.create_index([("user_id", 1), ("ticker", 1)], unique=True)
    await db.alerts.create_index([("user_id", 1), ("created_at", -1)])
    await db.scan_logs.create_index("started_at", expireAfterSeconds=2592000)  # 30-day TTL

    print(f"[✓] Connected to MongoDB: {settings.DATABASE_NAME}")


async def close_db():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("[✓] MongoDB connection closed")


def get_db():
    """Get database instance."""
    return db
