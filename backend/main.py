"""
main.py
FastAPI application entry point.
"""

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
    allow_origins=settings.CORS_ORIGINS,
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
