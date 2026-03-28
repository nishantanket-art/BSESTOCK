import sys
import os
import asyncio

# Ensure parent directory is in path for backend imports
sys.path.append(os.getcwd())

from backend.database import connect_db, close_db
from backend.routers.scanner import _run_scan_pipeline

async def main():
    print("Connecting to database...")
    await connect_db()
    
    print("Starting full production scan pipeline (scraping → analyzing → persist)...")
    try:
        # Run the same pipeline the web UI triggers
        await _run_scan_pipeline()
        print("Success: Full scan complete!")
    except Exception as e:
        print(f"Error during scan: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Closing database (saving state if mock)...")
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())
