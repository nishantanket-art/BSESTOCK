import uvicorn
import sys
import os

# Add current directory to path so backend can be found
sys.path.append(os.getcwd())

if __name__ == "__main__":
    print("Starting PromoterAI Backend...")
    try:
        config = uvicorn.Config("backend.main:app", host="127.0.0.1", port=8001, log_level="debug", reload=False)
        server = uvicorn.Server(config)
        server.run()
    except SystemExit as se:
        print(f"Server exited with SystemExit: {se}")
    except Exception as e:
        print(f"FAILED TO START SERVER: {e}")
        import traceback
        traceback.print_exc()
