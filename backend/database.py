"""
database.py
MongoDB connection using Motor (async driver).
"""

from mongomock_motor import AsyncMongoMockClient
from backend.config import settings

client: AsyncMongoMockClient = None
db = None


async def connect_db():
    """Initialize MongoDB connection."""
    global client, db
    client = AsyncMongoMockClient()
    db = client[settings.DATABASE_NAME]

    # Create indexes
    await db.users.create_index("username", unique=True)
    await db.companies.create_index("ticker", unique=True)
    await db.holdings_history.create_index([("ticker", 1), ("scanned_at", -1)])
    await db.watchlists.create_index([("user_id", 1), ("ticker", 1)], unique=True)
    await db.alerts.create_index([("user_id", 1), ("created_at", -1)])
    await db.scan_logs.create_index("started_at", expireAfterSeconds=2592000)  # 30-day TTL

    print(f"[OK] Connected to MongoDB: {settings.DATABASE_NAME}")


async def close_db():
    """Close MongoDB connection."""
    global client
    if client:
        # client.close()  # mongomock doesn't need to close
        print("[OK] MongoDB connection closed")


def get_db():
    """Get database instance."""
    return db
