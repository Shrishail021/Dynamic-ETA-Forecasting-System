#!/usr/bin/env python3
"""
Multi-Model Training & Benchmark Suite for RailPulse.
Trains and compares multiple machine learning regressors on the chronological train/test split:
  1. Naive Schedule Baseline (Persistence + Halt Recovery)
  2. Ridge Linear Regressor (L2 Regularized)
  3. Random Forest Regressor (Ensemble Bagging)
  4. HistGradientBoosting Regressor (Quantile P50 Median & P90 Uncertainty)
  5. HistGradientBoosting Regressor (MSE Point Estimate)

Saves models and metrics to ml/models/multi_model_comparison.json and joblib bundles.
"""

import json
from pathlib import Path
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "railway_eta_dataset" / "data" / "historical_journeys.csv"
MODELS_DIR = ROOT / "ml" / "models"
COMPARISON_OUT = MODELS_DIR / "multi_model_comparison.json"

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
NUMERIC_COLUMNS = [c for c in FEATURE_COLUMNS if c not in CATEGORICAL_COLUMNS]


def load_dataset():
    df = pd.read_csv(DATA_PATH, dtype={"train_no": str}, parse_dates=["journey_date"])
    for col in CATEGORICAL_COLUMNS:
        df[col] = df[col].astype("category")
    return df


def main():
    print("=" * 72)
    print(" RailPulse Multi-Model Training & Benchmark Suite")
    print("=" * 72)

    df = load_dataset()
    dates = sorted(df["journey_date"].unique())
    cutoff = dates[int(len(dates) * 0.8)]

    train_df = df[df["journey_date"] < cutoff]
    test_df = df[df["journey_date"] >= cutoff]

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[TARGET]
    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET]

    print(f"[*] Training samples: {len(X_train)} | Test samples: {len(X_test)}")
    print(f"[*] Chronological cutoff date: {cutoff.strftime('%Y-%m-%d')}\n")

    results = []

    # -------------------------------------------------------------
    # 1. Naive Baseline (Current Railway Standard)
    # -------------------------------------------------------------
    print("[1/5] Evaluating Naive Schedule Baseline...")
    recovery = (test_df["halt_min_scheduled"] >= 5) * 5.0
    naive_pred = (test_df["prev_station_arrival_delay_min"] - recovery).clip(lower=0)
    naive_mae = float(mean_absolute_error(y_test, naive_pred))
    naive_rmse = float(np.sqrt(mean_squared_error(y_test, naive_pred)))
    naive_r2 = float(r2_score(y_test, naive_pred))
    results.append({
        "model": "Naive Baseline (Schedule + Buffer)",
        "type": "Heuristic Rule",
        "mae_min": round(naive_mae, 2),
        "rmse_min": round(naive_rmse, 2),
        "r2_score": round(naive_r2, 3),
        "improvement_pct": 0.0,
        "uncertainty_support": "No (Fixed buffer)",
    })

    # -------------------------------------------------------------
    # 2. Ridge Linear Regression (L2 Regularized)
    # -------------------------------------------------------------
    print("[2/5] Training Ridge Linear Regressor...")
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_COLUMNS),
            ("num", "passthrough", NUMERIC_COLUMNS),
        ]
    )
    ridge_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", Ridge(alpha=10.0)),
    ])
    ridge_pipeline.fit(X_train, y_train)
    ridge_pred = ridge_pipeline.predict(X_test)
    ridge_mae = float(mean_absolute_error(y_test, ridge_pred))
    ridge_rmse = float(np.sqrt(mean_squared_error(y_test, ridge_pred)))
    ridge_r2 = float(r2_score(y_test, ridge_pred))
    results.append({
        "model": "Ridge Linear Regressor",
        "type": "Linear (L2)",
        "mae_min": round(ridge_mae, 2),
        "rmse_min": round(ridge_rmse, 2),
        "r2_score": round(ridge_r2, 3),
        "improvement_pct": round((naive_mae - ridge_mae) / naive_mae * 100, 1),
        "uncertainty_support": "No",
    })
    joblib.dump(ridge_pipeline, MODELS_DIR / "ridge_model.joblib")

    # -------------------------------------------------------------
    # 3. Random Forest Regressor (Ensemble Bagging)
    # -------------------------------------------------------------
    print("[3/5] Training Random Forest Regressor (100 trees)...")
    # For RF, convert categorical to numeric codes for fast training
    X_train_rf = X_train.copy()
    X_test_rf = X_test.copy()
    for col in CATEGORICAL_COLUMNS:
        X_train_rf[col] = X_train_rf[col].cat.codes
        X_test_rf[col] = X_test_rf[col].cat.codes

    rf_model = RandomForestRegressor(n_estimators=100, max_depth=16, random_state=42, n_jobs=-1)
    rf_model.fit(X_train_rf, y_train)
    rf_pred = rf_model.predict(X_test_rf)
    rf_mae = float(mean_absolute_error(y_test, rf_pred))
    rf_rmse = float(np.sqrt(mean_squared_error(y_test, rf_pred)))
    rf_r2 = float(r2_score(y_test, rf_pred))
    results.append({
        "model": "Random Forest Regressor",
        "type": "Tree Bagging Ensemble",
        "mae_min": round(rf_mae, 2),
        "rmse_min": round(rf_rmse, 2),
        "r2_score": round(rf_r2, 3),
        "improvement_pct": round((naive_mae - rf_mae) / naive_mae * 100, 1),
        "uncertainty_support": "Estimator Variance",
    })
    joblib.dump(rf_model, MODELS_DIR / "random_forest_model.joblib")

    # -------------------------------------------------------------
    # 4. HistGradientBoosting Regressor (Point Estimate / Squared Error)
    # -------------------------------------------------------------
    print("[4/5] Training HistGradientBoosting (Squared Error)...")
    hgb_mse = HistGradientBoostingRegressor(
        loss="squared_error",
        categorical_features=CATEGORICAL_COLUMNS,
        max_iter=150,
        random_state=42
    )
    hgb_mse.fit(X_train, y_train)
    hgb_pred = hgb_mse.predict(X_test)
    hgb_mae = float(mean_absolute_error(y_test, hgb_pred))
    hgb_rmse = float(np.sqrt(mean_squared_error(y_test, hgb_pred)))
    hgb_r2 = float(r2_score(y_test, hgb_pred))
    results.append({
        "model": "HistGradientBoosting (Point Estimate)",
        "type": "Gradient Boosted Trees",
        "mae_min": round(hgb_mae, 2),
        "rmse_min": round(hgb_rmse, 2),
        "r2_score": round(hgb_r2, 3),
        "improvement_pct": round((naive_mae - hgb_mae) / naive_mae * 100, 1),
        "uncertainty_support": "No (Mean only)",
    })
    joblib.dump(hgb_mse, MODELS_DIR / "hgb_point_model.joblib")

    # -------------------------------------------------------------
    # 5. HistGradientBoosting Quantile Models (P50 & P90) - Primary RailPulse Engine
    # -------------------------------------------------------------
    print("[5/5] Training HistGradientBoosting Quantile Models (P50 Median & P90 Upper Bound)...")
    model_p50 = HistGradientBoostingRegressor(
        loss="quantile",
        quantile=0.5,
        categorical_features=CATEGORICAL_COLUMNS,
        max_iter=150,
        random_state=42
    )
    model_p50.fit(X_train, y_train)

    model_p90 = HistGradientBoostingRegressor(
        loss="quantile",
        quantile=0.9,
        categorical_features=CATEGORICAL_COLUMNS,
        max_iter=150,
        random_state=42
    )
    model_p90.fit(X_train, y_train)

    p50_pred = model_p50.predict(X_test)
    p90_pred = model_p90.predict(X_test)

    p50_mae = float(mean_absolute_error(y_test, p50_pred))
    p50_rmse = float(np.sqrt(mean_squared_error(y_test, p50_pred)))
    p50_r2 = float(r2_score(y_test, p50_pred))
    p90_coverage = float(np.mean(y_test <= p90_pred))

    results.append({
        "model": "HistGradientBoosting (Quantile P50 / P90)",
        "type": "Quantile Gradient Boosted Trees",
        "mae_min": round(p50_mae, 2),
        "rmse_min": round(p50_rmse, 2),
        "r2_score": round(p50_r2, 3),
        "improvement_pct": round((naive_mae - p50_mae) / naive_mae * 100, 1),
        "uncertainty_support": f"Yes (P90 Empirical Coverage: {p90_coverage*100:.1f}%)",
        "is_primary": True,
    })

    # Save primary bundle for backend
    primary_bundle = {
        "model_p50": model_p50,
        "model_p90": model_p90,
        "feature_columns": FEATURE_COLUMNS,
        "categorical_columns": CATEGORICAL_COLUMNS,
        "target": TARGET,
        "trained_at": datetime.now().isoformat(),
    }
    joblib.dump(primary_bundle, MODELS_DIR / "eta_gbm_model.joblib")

    # -------------------------------------------------------------
    # Print Leaderboard Table
    # -------------------------------------------------------------
    print("\n" + "=" * 84)
    print(f"{'Model Architecture':<36} | {'Type':<20} | {'MAE (min)':<9} | {'Improv %':<8} | {'R2 Score':<8}")
    print("-" * 84)
    for r in sorted(results, key=lambda x: x["mae_min"]):
        print(f"{r['model']:<36} | {r['type']:<20} | {r['mae_min']:<9.2f} | {r['improvement_pct']:<8.1f} | {r['r2_score']:<8.3f}")
    print("=" * 84)

    # Save multi_model_comparison.json
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "leaderboard": sorted(results, key=lambda x: x["mae_min"]),
        "peer_reviewed_benchmark": {
            "citation": "arXiv 2510.01262 (RSTGCN)",
            "real_ir_mae_improvement": "13-15%",
            "note": "Synthetic data improvement (~78%) is inflated by deterministic simulation laws. Cite real IR benchmark during presentations."
        }
    }

    with open(COMPARISON_OUT, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n[OK] Comparative benchmark report saved to: {COMPARISON_OUT}")
    print("[OK] All model artifacts saved to: ml/models/")


if __name__ == "__main__":
    main()
