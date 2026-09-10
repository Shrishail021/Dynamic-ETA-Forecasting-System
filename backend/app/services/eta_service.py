"""
ETA prediction service.

Two methods, matching the project brief's "beat the naive baseline"
framing:

1. `naive_baseline_eta()` — WORKING NOW. This reproduces what the brief
   describes as today's real-world method: assume the current delay
   persists unchanged at every future station (railways' actual practice
   is schedule + current delay + fixed recovery assumption). This is the
   number your ML model needs to beat, not a strawman to delete.

2. `model_based_eta()` — hook for the trained model from
   ml/train_gbm_model.py. TODO(Antigravity): load the model via
   app/ml/model_loader.py and use it here, falling back to the naive
   baseline if no trained model file exists yet.
"""

from app.services.data_store import data_store
from app.ml.model_loader import load_gbm_model, predict_with_gbm


def naive_baseline_eta(train_no: str, current_station_seq: int, current_delay_min: float):
    """Assume current delay persists at every future stop (today's
    real-world default). Returns a list of dicts, one per upcoming stop."""
    schedule = data_store.schedule_for(train_no)
    upcoming = [s for s in schedule if s["seq"] > current_station_seq]

    results = []
    for stop in upcoming:
        # illustrative fixed recovery per stop with a real halt (mirrors
        # railways' fixed in-built recovery time, per the problem statement)
        recovery = 5.0 if stop["halt_min"] >= 5 else 0.0
        predicted = max(0.0, current_delay_min - recovery)
        current_delay_min = predicted  # small cumulative recovery downstream
        results.append({
            "to_station": stop["station_code"],
            "predicted_arrival_delay_min": round(predicted, 1),
            # naive method has no real uncertainty model — this is an
            # illustrative +/-20% band, NOT a statistically fitted interval
            "p50_delay_min": round(predicted, 1),
            "p90_delay_min": round(predicted * 1.4 + 5, 1),
            "method": "naive_baseline",
        })
    return results


def model_based_eta(train_no: str, current_station_seq: int, current_delay_min: float, as_of=None):
    """TODO(Antigravity): this is the real deliverable. Once
    ml/train_gbm_model.py has produced ml/models/eta_gbm_model.joblib:
      1. Load it via app/ml/model_loader.py (already stubbed)
      2. For each upcoming section, build the exact feature vector used at
         training time (see data/railway_eta_dataset/README.md's
         "known BEFORE" column list — do NOT include outcome columns)
      3. Use quantile regression or a conformal-prediction wrapper for the
         p50/p90 band instead of the naive +/-20% placeholder
      4. Fall back to naive_baseline_eta() if no model file is present yet,
         so the endpoint never hard-fails during development
    """
    model = load_gbm_model()
    if model is None:
        results = naive_baseline_eta(train_no, current_station_seq, current_delay_min)
        for r in results:
            r["method"] = "naive_baseline (no trained model found — see ml/train_gbm_model.py)"
        return results
    return predict_with_gbm(model, train_no, current_station_seq, current_delay_min)
