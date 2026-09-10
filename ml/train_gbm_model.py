#!/usr/bin/env python3
"""
Trains the real ETA model: two HistGradientBoostingRegressor quantile
models (P50 and P90) predicting arrival_delay_min, using ONLY the
"known before the section happens" columns documented in
data/railway_eta_dataset/README.md — see FEATURE_COLUMNS below. This is
deliberately leakage-safe: it does not use weather_condition,
speed_anomaly_flag, actual_running_min, etc., because those describe the
OUTCOME of the section you're trying to predict.

Uses sklearn's HistGradientBoostingRegressor rather than XGBoost/LightGBM
to keep the foundation dependency-light (it's built into scikit-learn and
supports native categorical handling + quantile loss out of the box).
Swap in XGBoost/LightGBM later if you want — same feature set applies.

Split is chronological (train on the first 80% of dates, test on the last
20%), not random, so the reported MAE reflects genuine forecasting
performance rather than leaking future information backward.

Run:
    python3 train_gbm_model.py

Writes:
    ml/models/eta_gbm_model.joblib   (used by the backend)
    ml/models/gbm_metrics.json       (MAE + comparison vs baseline)
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "railway_eta_dataset" / "data" / "historical_journeys.csv"
MODEL_OUT = Path(__file__).resolve().parent / "models" / "eta_gbm_model.joblib"
METRICS_OUT = Path(__file__).resolve().parent / "models" / "gbm_metrics.json"

TARGET = "arrival_delay_min"

# "Known BEFORE the section outcome" -- see data/railway_eta_dataset/README.md
# for the full leakage explanation. Do not add weather_condition,
# actual_running_min, section_avg_speed_kmph, speed_anomaly_flag,
# is_tsr_event, recovered_min, or visibility_m/temperature_c here.
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


def load_data():
    df = pd.read_csv(DATA_PATH, dtype={"train_no": str}, parse_dates=["journey_date"])
    for col in CATEGORICAL_COLUMNS:
        df[col] = df[col].astype("category")
    return df


def chronological_split(df, test_frac=0.2):
    dates = sorted(df["journey_date"].unique())
    cutoff = dates[int(len(dates) * (1 - test_frac))]
    train_df = df[df["journey_date"] < cutoff]
    test_df = df[df["journey_date"] >= cutoff]
    return train_df, test_df


def baseline_mae_on(df):
    recovery = (df["halt_min_scheduled"] >= 5) * 5.0
    pred = (df["prev_station_arrival_delay_min"] - recovery).clip(lower=0)
    return mean_absolute_error(df[TARGET], pred)


def main():
    df = load_data()
    train_df, test_df = chronological_split(df)
    print(f"train rows: {len(train_df)}  test rows: {len(test_df)}")

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df[TARGET]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df[TARGET]

    cat_mask = [c in CATEGORICAL_COLUMNS for c in FEATURE_COLUMNS]

    model_p50 = HistGradientBoostingRegressor(
        loss="quantile", quantile=0.5, categorical_features=cat_mask,
        max_iter=300, learning_rate=0.06, random_state=42,
    ).fit(X_train, y_train)

    model_p90 = HistGradientBoostingRegressor(
        loss="quantile", quantile=0.9, categorical_features=cat_mask,
        max_iter=300, learning_rate=0.06, random_state=42,
    ).fit(X_train, y_train)

    pred_p50 = model_p50.predict(X_test)
    pred_p90 = model_p90.predict(X_test)

    gbm_mae = mean_absolute_error(y_test, pred_p50)
    baseline_mae = baseline_mae_on(test_df)
    coverage_p90 = float(np.mean(y_test.values <= pred_p90))  # should land near 0.90

    metrics = {
        "n_train": len(train_df), "n_test": len(test_df),
        "gbm_p50_mae_min": round(gbm_mae, 2),
        "naive_baseline_mae_min": round(baseline_mae, 2),
        "improvement_pct": round(100 * (baseline_mae - gbm_mae) / baseline_mae, 1),
        "p90_empirical_coverage": round(coverage_p90, 3),
        "feature_columns": FEATURE_COLUMNS,
        "note": "MAE on a chronological (not random) train/test split, on "
                "simulated/prototype data. IMPORTANT: the ~79% improvement "
                "figure is inflated relative to what's achievable on real "
                "data -- this synthetic dataset's noise process (fog, "
                "congestion, TSR) is fully determined by the features the "
                "model was given, so the model can partially reverse-"
                "engineer the generator itself. On real Indian Railways "
                "data, expect a much smaller (but still real) improvement, "
                "in line with the 13-15% MAE improvement reported by peer- "
                "reviewed work on real IR delay data (RSTGCN, arXiv "
                "2510.01262). State this caveat explicitly in your SIH "
                "submission -- judges who understand ML will ask, and "
                "volunteering it first reads as rigor, not weakness.",
    }

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "model_p50": model_p50, "model_p90": model_p90,
        "feature_columns": FEATURE_COLUMNS,
        "categorical_columns": CATEGORICAL_COLUMNS,
    }, MODEL_OUT)

    with open(METRICS_OUT, "w") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps(metrics, indent=2))
    print(f"\nSaved model to {MODEL_OUT}")


if __name__ == "__main__":
    main()
