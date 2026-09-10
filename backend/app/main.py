"""
Dynamic ETA Forecasting — RailPulse Backend (SIH PS 26028)
FastAPI application with SQLite persistence, JWT authentication,
dynamic live re-forecasting, control room telemetry, and ML quantile models.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import public_trains, eta, live, admin_trains, auth, control_room, telemetry, station_master
from app.core.config import settings
from app.db.database import init_db
from app.services.data_store import data_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite schema and seed CSVs on startup
    init_db()
    data_store.ensure_loaded()
    yield


app = FastAPI(
    title="RailPulse — Dynamic ETA Forecasting System",
    description="Backend API for Indian Railways coaching trains dynamic ETA forecasting.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registrations
app.include_router(public_trains.router, prefix="/api/trains", tags=["public: trains"])
app.include_router(eta.router, prefix="/api/eta", tags=["public: eta"])
app.include_router(live.router, prefix="/api/live", tags=["public: live feed"])
app.include_router(admin_trains.router, prefix="/api/admin/trains", tags=["admin: train master"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(control_room.router, prefix="/api/control-room", tags=["staff: control room"])
app.include_router(telemetry.router, prefix="/api/telemetry", tags=["telemetry & metrics"])
app.include_router(station_master.router, prefix="/api/station-master", tags=["station master: monitoring & broadcast"])


@app.get("/", tags=["meta"])
def root_index():
    return {
        "system": "RailPulse Dynamic ETA Forecasting Engine",
        "status": "online",
        "interactive_docs": "/docs",
        "health_check": "/api/health",
        "frontend_ui_url": "http://localhost:5173",
        "note": "Open http://localhost:5173 in your browser to view the RailPulse frontend dashboard."
    }


@app.get("/api", tags=["meta"])
def api_index():
    return {
        "status": "ok",
        "endpoints": {
            "trains": "/api/trains",
            "predict_eta": "/api/eta/predict",
            "live_stream": "/api/live/{train_no}/stream",
            "control_room": "/api/control-room/overview",
            "admin_trains": "/api/admin/trains",
            "auth": "/api/auth/login",
            "telemetry_metrics": "/api/telemetry/model-metrics",
            "telemetry_export": "/api/telemetry/export.sql",
        }
    }


@app.get("/api/health", tags=["meta"])
def health_check():
    return {
        "status": "ok",
        "system": "RailPulse Dynamic ETA Forecasting Engine",
        "database_connected": settings.DATABASE_PATH.exists(),
        "database_path": str(settings.DATABASE_PATH),
        "model_loaded": settings.GBM_MODEL_PATH.exists(),
        "disclaimer": "Prototype system running on simulated/synthetic telemetry data — not real Indian Railways operational data. Built for SIH PS 26028.",
    }

