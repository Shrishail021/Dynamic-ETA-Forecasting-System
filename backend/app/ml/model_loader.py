"""
Loads the trained model artifact produced by ml/train_gbm_model.py and
builds real feature vectors for inference.
Implements autoregressive ML chaining across upcoming sections (Task 7):
each predicted section delay feeds into the subsequent section's previous-station
delay and rolling 3-station average.
"""

from datetime import datetime, date
import sys
from pathlib import Path
import joblib
import pandas as pd

from app.core.config import settings
from app.services.data_store import data_store

# Dynamic import for dynamics helper if available
_dataset_pkg = str(settings.DATASET_PKG_DIR)
if _dataset_pkg not in sys.path:
    sys.path.insert(0, _dataset_pkg)

try:
    from railway_sim.dynamics import is_festival_season, season_of
except Exception:
    def is_festival_season(d: date) -> bool:
        return (d.month in (10, 11) and 15 <= d.day <= 30) or (d.month == 3 and 1 <= d.day <= 20)

    def season_of(d: date) -> str:
        if d.month in (12, 1, 2):
            return "winter"
        if d.month in (6, 7, 8, 9):
            return "monsoon"
        return "other"


def load_gbm_model():
    if not settings.GBM_MODEL_PATH.exists():
        return None
    try:
        return joblib.load(settings.GBM_MODEL_PATH)
    except Exception as e:
        print(f"Warning: Could not load GBM model bundle from {settings.GBM_MODEL_PATH}: {e}")
        return None


def predict_with_gbm(model_bundle, train_no: str, current_station_seq: int,
                     current_delay_min: float, as_of: str = None):
    """
    Autoregressively predicts arrival delay for all upcoming sections.
    Each section's predicted p50 delay cascades as the upstream delay
    for the subsequent section, capturing real compounding delay dynamics.
    """
    data_store.ensure_loaded()
    feature_columns = model_bundle["feature_columns"]
    categorical_columns = model_bundle.get("categorical_columns") or model_bundle.get("low_card_columns", ["season"])
    model_p50 = model_bundle["model_p50"]
    model_p90 = model_bundle["model_p90"]

    train_row = data_store.train_row(train_no)
    if not train_row:
        return []

    schedule = data_store.schedule_for(train_no)
    sections = data_store.sections_for_route(train_row["route_id"])

    when = datetime.fromisoformat(as_of) if as_of else datetime.now()
    origin_h, origin_m = map(int, str(train_row["origin_departure_time"]).split(":"))

    upcoming_sections = [s for s in sections if s["seq"] > current_station_seq]
    upcoming_stops = {s["seq"]: s for s in schedule if s["seq"] > current_station_seq}

    results = []
    rolling_window = [float(current_delay_min)]
    prev_delay = float(current_delay_min)

    # Autoregressive forward chaining loop
    for sec in upcoming_sections:
        stop = upcoming_stops.get(sec["seq"])
        if stop is None:
            continue

        dep_minutes_from_origin = stop["scheduled_departure_min"] - stop["halt_min"]
        dep_hour = (origin_h + (origin_m + int(dep_minutes_from_origin)) // 60) % 24

        rolling_avg = sum(rolling_window[-3:]) / len(rolling_window[-3:])

        total_route_distance = float(schedule[-1]["distance_from_origin_km"]) if schedule else 1000.0
        dist_from_origin = float(stop.get("distance_from_origin_km", 0.0))
        distance_remaining = max(0.0, total_route_distance - dist_from_origin)
        stops_remaining = max(0, len(upcoming_sections) - (sec["seq"] - current_station_seq))

        feature_row = {
            "train_no": str(train_no),
            "train_type": train_row.get("train_type", "express"),
            "priority": int(train_row.get("priority", 2)),
            "day_of_week": when.weekday(),
            "month": when.month,
            "season": season_of(when.date()),
            "is_festival_day": bool(is_festival_season(when.date())),
            "station_seq": int(sec["seq"]),
            "from_station": str(sec["from_code"]),
            "to_station": str(sec["to_code"]),
            "distance_from_origin_km": dist_from_origin,
            "section_distance_km": float(sec.get("distance_km", 50.0)),
            "distance_remaining": distance_remaining,
            "number_of_stops_remaining": stops_remaining,
            "scheduled_arrival_min_from_origin": float(stop.get("scheduled_arrival_min", 0)),
            "scheduled_departure_min_from_origin": float(stop.get("scheduled_departure_min", 0)),
            "halt_min_scheduled": float(sec.get("halt_min_at_to", stop.get("halt_min", 2))),
            "section_permissible_speed_kmph": float(sec.get("permissible_speed_kmph", 110)),
            "section_scheduled_avg_speed_kmph": float(sec.get("scheduled_avg_speed_kmph", 80)),
            "fog_prone_section": bool(sec.get("fog_prone", False)),
            "congestion_level_static": float(sec.get("congestion_level", 0.5)),
            "departure_hour_of_day": int(dep_hour),
            "historical_avg_delay_min": float(stop.get("historical_avg_delay_min", 15.0)),
            "prev_station_arrival_delay_min": float(prev_delay),
            "rolling_avg_delay_last3_min": float(rolling_avg),
            "temperature_c": 25.0,
            "precipitation_mm": 0.0,
        }

        # Create single-row DataFrame for prediction
        X_df = pd.DataFrame([feature_row])

        # Handle encoder if model bundle uses TargetEncoder
        if "encoder" in model_bundle:
            high_card = model_bundle.get("high_card_columns", ["train_no", "from_station", "to_station"])
            try:
                X_df[high_card] = model_bundle["encoder"].transform(X_df[high_card])
            except Exception:
                pass

        # Handle categorical columns
        cat_cols = model_bundle.get("low_card_columns") or categorical_columns
        for col in cat_cols:
            if col in X_df.columns:
                X_df[col] = X_df[col].astype("category")

        # Keep strictly feature_columns in correct order
        X_input = X_df[feature_columns]

        p50_raw = float(model_p50.predict(X_input)[0])
        p90_raw = float(model_p90.predict(X_input)[0])

        p50 = max(0.0, p50_raw)
        p90 = max(p50, p90_raw)

        results.append({
            "to_station": sec["to_code"],
            "predicted_arrival_delay_min": round(p50, 1),
            "p50_delay_min": round(p50, 1),
            "p90_delay_min": round(p90, 1),
            "method": "gbm_model (autoregressive chaining)",
        })

        # Autoregressive forward step: feed the predicted p50 delay forward
        prev_delay = p50
        rolling_window.append(p50)

    return results
