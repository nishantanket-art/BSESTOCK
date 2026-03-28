"""
main.py
FastAPI application entry point.
"""

import sys
import os

# Add the root project directory to sys.path so 'backend.*' imports resolve
# This is critical for Render deployments when the start command is 'python backend/main.py'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import connect_db, close_db
from backend.routers import auth, stocks, watchlist, alerts, scanner


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect DB on start, close on shutdown."""
    try:
        await connect_db()
        print("[OK] Application started successfully")
    except Exception as e:
        print(f"[WARNING] Startup error (non-fatal): {e}")
    yield
    try:
        await close_db()
    except Exception as e:
        print(f"[WARNING] Shutdown error: {e}")


app = FastAPI(
    title="Promoter Stake AI Platform",
    description="AI-powered financial monitoring platform for tracking promoter shareholding patterns in Indian stocks",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*", 
        "https://bsestock-frontend.onrender.com",
        "https://bsestock-ui.onrender.com",
        "https://bsestock.onrender.com",
        "http://localhost:5173",
        "http://localhost:3000",
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(watchlist.router)
app.include_router(alerts.router)
app.include_router(scanner.router)


@app.get("/")
async def root():
    return {
        "name": "Promoter Stake AI Platform",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    # Render provides the PORT environment variable natively
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)
