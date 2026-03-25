import sys
import asyncio

# add pr to path so backend imports work
sys.path.append(r"d:\pr")

from backend.database import connect_db

async def main():
    try:
        await connect_db()
        print("SUCCESS")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
