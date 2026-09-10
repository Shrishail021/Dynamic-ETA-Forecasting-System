#!/usr/bin/env python3
"""
Retrains the P50/P90 quantile GBM models using both:
1. Base historical journeys dataset (historical_journeys.csv)
2. Newly captured journey telemetry & completed arrival events from SQLite (backend/data/railpulse.db)

Outputs updated:
- ml/models/eta_gbm_model.joblib
- ml/models/gbm_metrics.json
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "railway_eta_dataset" / "data" / "historical_journeys.csv"
DB_PATH = ROOT / "backend" / "data" / "railpulse.db"
MODEL_OUT = Path(__file__).resolve().parent / "models" / "eta_gbm_model.joblib"
METRICS_OUT = Path(__file__).resolve().parent / "models" / "gbm_metrics.json"

TARGET = "arrival_delay_min"

FEATURE_COLUMNS = [
    "train_type", "priority", "day_of_week", "month", "season",
    "is_festival_day", "station_seq", "from_station", "to_station",
    "distance_from_origin_km", "section_distance_km",
    "scheduled_arrival_min_from_origin", "scheduled_departure_min_from_origin",
    "halt_min_scheduled", "section_permissible_speed_kmph",
    "section_scheduled_avg_speed_kmph", "fog_prone_section",
    "congestion_level_static", "departure_hour_of_day",
    "prev_station_arrival_delay_min", "rolling_avg_delay_last3_min",
]

CATEGORICAL_COLUMNS = ["train_type", "season", "from_station", "to_station"]


def load_combined_dataset():
    print(f"[*] Loading historical dataset from {DATA_PATH}...")
    df_hist = pd.read_csv(DATA_PATH, dtype={"train_no": str}, parse_dates=["journey_date"])

    # Attempt to load newly logged arrival telemetry from SQLite
    new_records = []
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT raw_payload FROM journey_telemetry_log
                WHERE event_type = 'arrival' AND actual_delay_min IS NOT NULL
            """)
            rows = cursor.fetchall()
            for (raw_json,) in rows:
                if not raw_json:
                    continue
                try:
                    payload = json.loads(raw_json)
                    # Check if all required feature fields exist in payload
                    if all(k in payload for k in FEATURE_COLUMNS) and TARGET in payload:
                        new_records.append({col: payload[col] for col in FEATURE_COLUMNS + [TARGET, "journey_date"]})
                except Exception:
                    pass
            conn.close()
            print(f"[*] Found {len(new_records)} newly captured operational records in SQLite database.")
        except Exception as e:
            print(f"[!] Warning reading from SQLite: {e}")

    if new_records:
        df_new = pd.DataFrame(new_records)
        df_new["journey_date"] = pd.to_datetime(df_new["journey_date"])
        combined_df = pd.concat([df_hist, df_new], ignore_index=True)
        print(f"[*] Combined dataset total rows: {len(combined_df)} (Historical: {len(df_hist)}, New: {len(new_records)})")
    else:
        combined_df = df_hist
        print(f"[*] Training solely on historical dataset ({len(combined_df)} rows).")

    for col in CATEGORICAL_COLUMNS:
        combined_df[col] = combined_df[col].astype("category")

    return combined_df


def main():
    print("=" * 60)
    print(" RailPulse ML Retraining Pipeline (With Live Telemetry)")
    print("=" * 60)

    df = load_combined_dataset()

    # Chronological 80/20 train/test split
    dates = sorted(df["journey_date"].unique())
    cutoff = dates[int(len(dates) * 0.8)]
    train_df = df[df["journey_date"] < cutoff]
    test_df = df[df["journey_date"] >= cutoff]

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[TARGET]
    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET]

    print(f"[*] Training P50 (median) quantile model on {len(X_train)} samples...")
    model_p50 = HistGradientBoostingRegressor(
        loss="quantile",
        quantile=0.5,
        categorical_features=CATEGORICAL_COLUMNS,
        max_iter=150,
        random_state=42,
    )
    model_p50.fit(X_train, y_train)

    print(f"[*] Training P90 (upper bound) quantile model on {len(X_train)} samples...")
    model_p90 = HistGradientBoostingRegressor(
        loss="quantile",
        quantile=0.9,
        categorical_features=CATEGORICAL_COLUMNS,
        max_iter=150,
        random_state=42,
    )
    model_p90.fit(X_train, y_train)

    # Evaluation
    pred_p50 = model_p50.predict(X_test)
    pred_p90 = model_p90.predict(X_test)

    p50_mae = float(mean_absolute_error(y_test, pred_p50))
    # Naive schedule baseline on test split: assume prev_station delay persists
    naive_pred = X_test["prev_station_arrival_delay_min"]
    naive_mae = float(mean_absolute_error(y_test, naive_pred))
    improvement = float((naive_mae - p50_mae) / naive_mae * 100)
    p90_coverage = float(np.mean(y_test <= pred_p90))

    print("-" * 60)
    print(f"GBM P50 MAE:          {p50_mae:.2f} min")
    print(f"Naive Baseline MAE:   {naive_mae:.2f} min")
    print(f"MAE Improvement:      {improvement:.1f}%")
    print(f"P90 Band Coverage:    {p90_coverage:.3f} (target: 0.900)")
    print("-" * 60)

    # Save bundle
    bundle = {
        "model_p50": model_p50,
        "model_p90": model_p90,
        "feature_columns": FEATURE_COLUMNS,
        "categorical_columns": CATEGORICAL_COLUMNS,
        "target": TARGET,
        "updated_at": datetime.now().isoformat(),
    }
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, MODEL_OUT)
    print(f"[OK] Saved updated model bundle to: {MODEL_OUT}")

    metrics = {
        "n_train": len(train_df),
        "n_test": len(test_df),
        "gbm_p50_mae_min": round(p50_mae, 2),
        "naive_baseline_mae_min": round(naive_mae, 2),
        "improvement_pct": round(improvement, 1),
        "p90_empirical_coverage": round(p90_coverage, 3),
        "feature_columns": FEATURE_COLUMNS,
        "last_retrained_at": datetime.now().isoformat(),
        "note": "Trained on combined historical + newly captured SQLite telemetry. Cite arXiv 2510.01262 peer-reviewed benchmark (13-15% improvement on real IR data) alongside synthetic results."
    }
    with open(METRICS_OUT, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[OK] Saved metrics to: {METRICS_OUT}")


if __name__ == "__main__":
    main()
