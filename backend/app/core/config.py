"""
Central config for RailPulse Dynamic ETA Forecasting Backend.
Loads environment variables with fallback defaults.
"""

from pathlib import Path
import os

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings:
    PROJECT_ROOT: Path = PROJECT_ROOT
    BACKEND_DIR: Path = BACKEND_DIR

    DATA_DIR: Path = PROJECT_ROOT / "data" / "railway_eta_dataset" / "data"
    DATASET_PKG_DIR: Path = PROJECT_ROOT / "data" / "railway_eta_dataset"

    # SQLite Database Persistence
    DB_DIR: Path = BACKEND_DIR / "data"
    DATABASE_PATH: Path = DB_DIR / "railpulse.db"
    SQL_EXPORT_PATH: Path = DB_DIR / "telemetry_export.sql"

    # ML models
    MODEL_DIR: Path = PROJECT_ROOT / "ml" / "models"
    BASELINE_METRICS_PATH: Path = MODEL_DIR / "baseline_metrics.json"
    GBM_MODEL_PATH: Path = MODEL_DIR / "eta_gbm_model.joblib"
    GBM_METRICS_PATH: Path = MODEL_DIR / "gbm_metrics.json"

    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

    # JWT Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "railpulse-super-secret-key-sih-2026-dynamic-eta")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Legacy demo token support for backwards compatibility
    DEMO_ADMIN_TOKEN: str = "demo-admin-token-change-me"


settings = Settings()
