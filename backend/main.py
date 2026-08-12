"""
FastAPI main application entry point.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import Base, engine
from config import get_settings
from routers import auth, destinations, tourist_load, carrying_capacity, itinerary, artisans, ai_chat, alerts, dashboard

settings = get_settings()

# ── Create tables ─────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Agentic AI platform for sustainable eco-tourism management in the Rann of Kutch. "
        "Powered by IBM Granite LLM and Machine Learning."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(destinations.router, prefix="/destinations", tags=["Destinations"])
app.include_router(tourist_load.router, prefix="/tourist-load", tags=["Tourist Load"])
app.include_router(carrying_capacity.router, prefix="/carrying-capacity", tags=["Carrying Capacity"])
app.include_router(itinerary.router, prefix="/itinerary", tags=["Itinerary"])
app.include_router(artisans.router, prefix="/artisans", tags=["Artisans & Community"])
app.include_router(ai_chat.router, prefix="/ai", tags=["AI Assistant"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])


@app.get("/", tags=["Health"])
def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "demo_mode": settings.demo_mode,
        "docs": "/docs",
        "note": "Smart Rann of Kutch Eco-Tourism & Carrying Capacity Planner — IBM Hackathon Project",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z"}
