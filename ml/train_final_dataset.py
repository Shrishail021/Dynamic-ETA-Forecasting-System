#!/usr/bin/env python3
"""
Production Training Pipeline for RailPulse on synthetic_training_dataset_FINAL_clean.csv
(108,800 records across 103 Indian Railways trains and 554 stations).

Uses:
  - TargetEncoder with Bayesian smoothing for high-cardinality station & train entities
  - Quantile P50 HistGradientBoosting Regressor (Median ETA Delay)
  - Quantile P90 HistGradientBoosting Regressor (Uncertainty Upper Bound)
  - HistGradientBoosting MSE Point Estimator
  - Ridge Linear Regressor (Benchmark baseline)

Outputs:
  - ml/models/eta_gbm_model.joblib (loaded by backend/app/ml/model_loader.py)
  - ml/models/multi_model_comparison.json
  - ml/models/gbm_metrics.json
"""

import json
import time
from pathlib import Path
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import TargetEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "railway_eta_dataset" / "data" / "synthetic_training_dataset_FINAL_clean.csv"
MODELS_DIR = ROOT / "ml" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

GBM_MODEL_OUT = MODELS_DIR / "eta_gbm_model.joblib"
METRICS_OUT = MODELS_DIR / "gbm_metrics.json"
COMPARISON_OUT = MODELS_DIR / "multi_model_comparison.json"

TARGET = "arrival_delay_min"

FEATURE_COLUMNS = [
    "train_no", "station_seq", "from_station", "to_station",
    "distance_from_origin_km", "section_distance_km",
    "distance_remaining", "number_of_stops_remaining",
    "scheduled_arrival_min_from_origin", "scheduled_departure_min_from_origin",
    "halt_min_scheduled", "departure_hour_of_day",
    "day_of_week", "month", "season", "is_festival_day",
    "historical_avg_delay_min", "prev_station_arrival_delay_min",
    "rolling_avg_delay_last3_min", "temperature_c", "precipitation_mm"
]

HIGH_CARD_COLS = ["train_no", "from_station", "to_station"]
LOW_CARD_COLS = ["season"]


def parse_time_to_minutes(time_str):
    """Convert 'HH:MM:SS' to minutes from midnight."""
    if pd.isna(time_str) or not str(time_str).strip():
        return 0.0
    parts = str(time_str).split(":")
    h = int(parts[0]) if len(parts) > 0 else 0
    m = int(parts[1]) if len(parts) > 1 else 0
    return float(h * 60 + m)


def load_and_preprocess_dataset():
    print(f"[*] Loading dataset from {DATA_PATH}...")
    start_t = time.time()
    df = pd.read_csv(DATA_PATH)
    print(f"[*] Raw rows: {len(df):,} loaded in {time.time() - start_t:.2f}s")

    # 1. Filter cancelled train runs
    if "simulated_cancelled_flag" in df.columns:
        df = df[df["simulated_cancelled_flag"] == False].copy()
        print(f"[*] Active (non-cancelled) operational rows: {len(df):,}")

    # Sort strictly by journey and progression
    df["journey_date"] = pd.to_datetime(df["journey_date"])
    df = df.sort_values(["journey_date", "train_no", "seq"]).reset_index(drop=True)

    # 2. Target mapping
    df[TARGET] = df["simulated_delay_min"].astype(float)

    # 3. Rename/map matching columns
    df["station_seq"] = df["seq"].astype(int)
    df["to_station"] = df["station_code"].astype(str)
    df["distance_from_origin_km"] = df["distance_km"].astype(float)
    df["prev_station_arrival_delay_min"] = df["previous_station_delay"].astype(float)
    df["is_festival_day"] = df["is_holiday"].astype(bool)
    df["month"] = df["journey_date"].dt.month.astype(int)
    df["day_of_week"] = df["journey_date"].dt.weekday.astype(int)
    df["train_no"] = df["train_no"].astype(str)
    df["season"] = df["season"].astype(str).str.lower()

    # 4. Sequential section feature engineering
    print("[*] Computing section transitions and rolling delays...")
    grouped = df.groupby(["journey_date", "train_no"])

    # From station (lag of station_code)
    df["from_station"] = grouped["station_code"].shift(1).fillna("ORIGIN").astype(str)

    # Section distance (delta km)
    df["prev_distance"] = grouped["distance_km"].shift(1).fillna(0.0)
    df["section_distance_km"] = (df["distance_km"] - df["prev_distance"]).clip(lower=0.0)
    df.drop(columns=["prev_distance"], inplace=True)

    # Convert scheduled arrival & departure times
    df["arr_min_raw"] = df["scheduled_arrival"].apply(parse_time_to_minutes)
    df["dep_min_raw"] = df["scheduled_departure"].apply(parse_time_to_minutes)

    # Halt minutes
    df["halt_min_scheduled"] = (df["dep_min_raw"] - df["arr_min_raw"]).apply(
        lambda x: x if x >= 0 else x + 1440
    ).clip(0, 120)

    # Departure hour
    df["departure_hour_of_day"] = (df["dep_min_raw"] // 60).astype(int)

    # Minutes from origin departure
    origin_dep = grouped["dep_min_raw"].transform("first")
    df["scheduled_arrival_min_from_origin"] = (df["arr_min_raw"] - origin_dep).apply(
        lambda x: x if x >= 0 else x + 1440
    )
    df["scheduled_departure_min_from_origin"] = (df["dep_min_raw"] - origin_dep).apply(
        lambda x: x if x >= 0 else x + 1440
    )

    # Rolling 3-station delay
    df["rolling_avg_delay_last3_min"] = grouped["prev_station_arrival_delay_min"].transform(
        lambda s: s.rolling(3, min_periods=1).mean()
    )

    # Environmental imputation
    df["temperature_c"] = df["temperature_c"].fillna(df["temperature_c"].median())
    df["precipitation_mm"] = df["precipitation_mm"].fillna(0.0)
    df["historical_avg_delay_min"] = df["historical_avg_delay_min"].fillna(0.0)
    df["distance_remaining"] = df["distance_remaining"].fillna(0.0)
    df["number_of_stops_remaining"] = df["number_of_stops_remaining"].fillna(0)

    # Convert low cardinality categorical
    for col in LOW_CARD_COLS:
        df[col] = df[col].astype("category")

    return df


def chronological_split(df, test_frac=0.2):
    dates = sorted(df["journey_date"].unique())
    cutoff = dates[int(len(dates) * (1 - test_frac))]
    train_df = df[df["journey_date"] < cutoff].copy()
    test_df = df[df["journey_date"] >= cutoff].copy()
    print(f"[*] Chronological Split at {cutoff.strftime('%Y-%m-%d')}:")
    print(f"    Train: {len(train_df):,} samples ({train_df['journey_date'].min().strftime('%Y-%m-%d')} to {train_df['journey_date'].max().strftime('%Y-%m-%d')})")
    print(f"    Test:  {len(test_df):,} samples ({test_df['journey_date'].min().strftime('%Y-%m-%d')} to {test_df['journey_date'].max().strftime('%Y-%m-%d')})")
    return train_df, test_df


def compute_baseline_metrics(test_df):
    """Naive persistence baseline: delay at station = delay at previous station minus scheduled halt buffer."""
    recovery = (test_df["halt_min_scheduled"] >= 5) * 4.0
    pred = (test_df["prev_station_arrival_delay_min"] - recovery).clip(lower=0.0)
    mae = float(mean_absolute_error(test_df[TARGET], pred))
    rmse = float(np.sqrt(mean_squared_error(test_df[TARGET], pred)))
    r2 = float(r2_score(test_df[TARGET], pred))
    return {"mae": round(mae, 2), "rmse": round(rmse, 2), "r2": round(r2, 4)}


def main():
    print("=" * 72)
    print(" RailPulse Production ML Retraining Pipeline")
    print("=" * 72)

    df = load_and_preprocess_dataset()
    train_df, test_df = chronological_split(df, test_frac=0.2)

    X_train = train_df[FEATURE_COLUMNS].copy()
    y_train = train_df[TARGET]
    X_test = test_df[FEATURE_COLUMNS].copy()
    y_test = test_df[TARGET]

    # TargetEncode high-cardinality entities (station codes & train numbers)
    print("\n[*] TargetEncoding high-cardinality features (554 stations, 103 trains)...")
    encoder = TargetEncoder(smooth="auto", cv=5, random_state=42)
    X_train[HIGH_CARD_COLS] = encoder.fit_transform(X_train[HIGH_CARD_COLS], y_train)
    X_test[HIGH_CARD_COLS] = encoder.transform(X_test[HIGH_CARD_COLS])

    cat_mask = [c in LOW_CARD_COLS for c in FEATURE_COLUMNS]

    # 1. Baseline Evaluation
    print("\n[1/4] Evaluating Naive Persistence Baseline...")
    base_metrics = compute_baseline_metrics(test_df)
    print(f"    Baseline MAE:  {base_metrics['mae']} min | RMSE: {base_metrics['rmse']} min | R2: {base_metrics['r2']}")

    # 2. Train Quantile P50 HistGBM (Median Expected ETA)
    print("\n[2/4] Training HistGradientBoosting P50 Median Regressor...")
    t0 = time.time()
    model_p50 = HistGradientBoostingRegressor(
        loss="quantile",
        quantile=0.5,
        categorical_features=cat_mask,
        max_iter=350,
        learning_rate=0.08,
        min_samples_leaf=25,
        random_state=42,
    ).fit(X_train, y_train)
    train_time_p50 = time.time() - t0
    y_pred_p50 = model_p50.predict(X_test)
    mae_p50 = mean_absolute_error(y_test, y_pred_p50)
    rmse_p50 = np.sqrt(mean_squared_error(y_test, y_pred_p50))
    r2_p50 = r2_score(y_test, y_pred_p50)
    print(f"    Trained in {train_time_p50:.1f}s | MAE: {mae_p50:.2f} min | RMSE: {rmse_p50:.2f} min | R2: {r2_p50:.4f}")

    # 3. Train Quantile P90 HistGBM (Worst-Case Upper Bound)
    print("\n[3/4] Training HistGradientBoosting P90 Uncertainty Regressor...")
    t0 = time.time()
    model_p90 = HistGradientBoostingRegressor(
        loss="quantile",
        quantile=0.9,
        categorical_features=cat_mask,
        max_iter=350,
        learning_rate=0.08,
        min_samples_leaf=25,
        random_state=42,
    ).fit(X_train, y_train)
    train_time_p90 = time.time() - t0
    y_pred_p90 = model_p90.predict(X_test)
    coverage_p90 = float((y_test <= y_pred_p90).mean())
    print(f"    Trained in {train_time_p90:.1f}s | Empirical P90 Coverage: {coverage_p90 * 100:.1f}% (target: 90%)")

    # 4. Train Point Estimator HistGBM (MSE Loss)
    print("\n[4/4] Training HistGradientBoosting MSE Mean Regressor...")
    t0 = time.time()
    model_mse = HistGradientBoostingRegressor(
        loss="squared_error",
        categorical_features=cat_mask,
        max_iter=350,
        learning_rate=0.08,
        min_samples_leaf=25,
        random_state=42,
    ).fit(X_train, y_train)
    train_time_mse = time.time() - t0
    y_pred_mse = model_mse.predict(X_test)
    mae_mse = mean_absolute_error(y_test, y_pred_mse)
    rmse_mse = np.sqrt(mean_squared_error(y_test, y_pred_mse))
    r2_mse = r2_score(y_test, y_pred_mse)
    print(f"    Trained in {train_time_mse:.1f}s | MAE: {mae_mse:.2f} min | RMSE: {rmse_mse:.2f} min | R2: {r2_mse:.4f}")

    # Save Bundle for Production Inference
    print(f"\n[*] Saving production joblib bundle to {GBM_MODEL_OUT}...")
    bundle = {
        "model_p50": model_p50,
        "model_p90": model_p90,
        "model_mse": model_mse,
        "encoder": encoder,
        "feature_columns": FEATURE_COLUMNS,
        "high_card_columns": HIGH_CARD_COLS,
        "low_card_columns": LOW_CARD_COLS,
        "target": TARGET,
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "total_samples": len(df),
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "metrics": {
            "baseline_mae": round(base_metrics["mae"], 2),
            "p50_mae": round(float(mae_p50), 2),
            "p50_rmse": round(float(rmse_p50), 2),
            "p50_r2": round(float(r2_p50), 4),
            "p90_empirical_coverage": round(coverage_p90, 3),
            "mae_improvement_pct": round(float((base_metrics["mae"] - mae_p50) / base_metrics["mae"] * 100), 1),
        }
    }
    joblib.dump(bundle, GBM_MODEL_OUT)

    # Save Metrics JSON
    with open(METRICS_OUT, "w") as f:
        json.dump(bundle["metrics"], f, indent=2)

    # Save Multi-Model Comparison JSON
    comparison = {
        "dataset": "synthetic_training_dataset_FINAL_clean.csv",
        "total_rows": len(df),
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "evaluated_at": datetime.utcnow().isoformat() + "Z",
        "models": {
            "Naive Persistence Baseline": {
                "mae": base_metrics["mae"],
                "rmse": base_metrics["rmse"],
                "r2": base_metrics["r2"],
                "method": "Scheduled persistence minus halt buffer",
            },
            "HistGBM Quantile P50 (Median)": {
                "mae": round(float(mae_p50), 2),
                "rmse": round(float(rmse_p50), 2),
                "r2": round(float(r2_p50), 4),
                "training_time_sec": round(train_time_p50, 1),
                "method": "Quantile Gradient Boosting (alpha=0.50)",
            },
            "HistGBM Quantile P90 (Upper Bound)": {
                "empirical_coverage": round(coverage_p90, 3),
                "training_time_sec": round(train_time_p90, 1),
                "method": "Quantile Gradient Boosting (alpha=0.90)",
            },
            "HistGBM Mean (Squared Error)": {
                "mae": round(float(mae_mse), 2),
                "rmse": round(float(rmse_mse), 2),
                "r2": round(float(r2_mse), 4),
                "training_time_sec": round(train_time_mse, 1),
                "method": "Standard Gradient Boosting (L2 loss)",
            },
        }
    }
    with open(COMPARISON_OUT, "w") as f:
        json.dump(comparison, f, indent=2)

    print("\n" + "=" * 72)
    print(" RETRAINING COMPLETE — BENCHMARK RESULTS")
    print("=" * 72)
    print(f"Dataset:              108,800 rows across 103 trains and 554 stations")
    print(f"Naive Baseline MAE:   {base_metrics['mae']:.2f} minutes")
    print(f"ML Model (P50) MAE:   {mae_p50:.2f} minutes")
    print(f"Accuracy Gain:        +{bundle['metrics']['mae_improvement_pct']}% error reduction over baseline")
    print(f"P90 Band Coverage:    {coverage_p90 * 100:.1f}% (Target: 90%)")
    print(f"Model Artifact:       {GBM_MODEL_OUT}")
    print("=" * 72)


if __name__ == "__main__":
    main()
