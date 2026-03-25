import sys
import os
import asyncio

# Add current directory to path
sys.path.append(os.getcwd())

async def test_lifespan():
    try:
        print("Attempting to import backend.main...")
        from backend.main import app
        print("Import successful!")
        
        print("Running lifespan startup...")
        async with app.router.lifespan_context(app):
            print("Lifespan startup successful!")
            print("Testing root endpoint...")
            from fastapi.testclient import TestClient
            client = TestClient(app)
            response = client.get("/")
            print(f"Response: {response.json()}")
            
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_lifespan())
