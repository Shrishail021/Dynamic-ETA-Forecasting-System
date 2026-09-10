#!/usr/bin/env python3
"""
Computes the "naive baseline" MAE on the historical dataset — the number
described in the project brief that any real ML model needs to beat.
Mirrors today's real-world method: assume the delay at departure from the
previous station persists unchanged (with a small fixed recovery at real
halts), and compare that assumption against what actually happened.

Run:
    python3 train_baseline_model.py

Writes ml/models/baseline_metrics.json.
"""

import json
import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "railway_eta_dataset" / "data" / "historical_journeys.csv"
OUT_PATH = Path(__file__).resolve().parent / "models" / "baseline_metrics.json"


def compute_baseline():
    df = pd.read_csv(DATA_PATH, dtype={"train_no": str})

    # Naive prediction: predicted_delay = prev_station_arrival_delay_min,
    # minus a fixed 5-minute recovery if this stop has a real scheduled
    # halt (halt_min_scheduled >= 5) -- exactly the logic in
    # backend/app/services/eta_service.naive_baseline_eta, kept identical
    # on purpose so this script's number matches what the API reports.
    recovery = (df["halt_min_scheduled"] >= 5) * 5.0
    df["naive_predicted_delay"] = (df["prev_station_arrival_delay_min"] - recovery).clip(lower=0)

    df["abs_error"] = (df["naive_predicted_delay"] - df["arrival_delay_min"]).abs()

    overall_mae = df["abs_error"].mean()
    by_type = df.groupby("train_type")["abs_error"].mean().to_dict()
    by_route = df.groupby("route_id")["abs_error"].mean().to_dict()

    metrics = {
        "method": "naive_baseline (persistence + fixed halt recovery)",
        "n_rows": len(df),
        "overall_mae_min": round(overall_mae, 2),
        "mae_by_train_type": {k: round(v, 2) for k, v in by_type.items()},
        "mae_by_route": {k: round(v, 2) for k, v in by_route.items()},
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    compute_baseline()
