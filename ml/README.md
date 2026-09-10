# ML — Baseline & Model Training

## Scripts

- `train_baseline_model.py` — computes the naive "persistence + fixed
  recovery" baseline MAE (mirrors what the problem statement says today's
  real-world ETA method does). This is the number you need to beat, not
  a strawman to throw away.
- `train_gbm_model.py` — trains two `HistGradientBoostingRegressor`
  quantile models (P50, P90) on leakage-safe features and saves them to
  `models/eta_gbm_model.joblib`, which the backend loads via
  `backend/app/ml/model_loader.py`.

## Current results (on the included synthetic dataset)

```
naive baseline MAE:     19.1 minutes
GBM (P50) MAE:            4.1 minutes
improvement:             ~79%
P90 band empirical coverage: 86% (target 90% — reasonably calibrated)
```

## Read this before you put the 79% number in your PPT

That improvement is **real on this dataset, but inflated relative to what's
achievable on real Indian Railways data**, and you should say so proactively
rather than let a judge catch it:

This synthetic dataset's delay-generating process (fog, congestion, TSR
events) is fully determined by columns the model is also given as features
(season, month, fog-prone flag, congestion level, departure hour...). A
gradient-boosted model can partially **reverse-engineer its own generator**
when given exactly the right variables — real train delay has unmodeled
confounders (crew decisions, freight priority conflicts, asset condition)
that no feature set fully captures. The peer-reviewed benchmark to actually
cite is the RSTGCN paper (arXiv 2510.01262) evaluated on real September
2024 Indian Railways data: **13–15% MAE improvement** over strong baselines.
Frame your number as "this validates the pipeline works end-to-end;
real-world improvement should be benchmarked against the ~13–15% range
reported in peer-reviewed work on real IR data" — that's a stronger, more
defensible claim than implying 79% is achievable in production.

## TODO(Antigravity)

1. Wire `backend/app/ml/model_loader.py::predict_with_gbm` to actually
   build the feature vector (currently a labeled placeholder) and call
   `model_p50`/`model_p90` from the saved bundle.
2. Consider adding a proper walk-forward / time-series cross-validation
   instead of a single chronological split, once you're tuning
   hyperparameters rather than just demoing.
3. If you get access to better calibration data (real fog frequency,
   real congestion stats for your target zone), retune the constants in
   `data/railway_eta_dataset/railway_sim/dynamics.py` rather than the ML
   model — the model is only as good as the process generating its
   training data.
