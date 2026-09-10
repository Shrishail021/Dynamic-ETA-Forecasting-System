# Architecture — Dynamic ETA Forecasting System

```
┌─────────────────────┐     ┌──────────────────────────────┐     ┌─────────────────┐
│  data/               │     │  backend/ (FastAPI)           │     │  frontend/       │
│  railway_eta_dataset │────▶│  - data_store.py (in-memory)  │◀───▶│  (Vite + React)  │
│  - historical CSVs   │     │  - eta_service.py              │     │  - public pages  │
│  - railway_sim/      │     │  - live_feed_service.py (SSE)  │     │  - admin pages   │
│    (shared dynamics) │     │  - admin_trains.py (CRUD)      │     │  - Stitch UI     │
│  - live_feed_        │     │  - auth.py (demo tokens)       │     │    drops in here │
│    simulator.py      │     └───────────────┬───────────────┘     └─────────────────┘
└─────────────────────┘                       │
           │                                  ▼
           │                     ┌──────────────────────────┐
           └────────────────────▶│  ml/                       │
                                  │  - train_baseline_model.py │
                                  │  - train_gbm_model.py       │
                                  │  - models/eta_gbm_model     │
                                  │    .joblib (P50/P90)        │
                                  └──────────────────────────┘
```

## Data flow for a live ETA prediction

1. Frontend calls `POST /api/eta/predict` with `train_no`, the last
   confirmed station (`current_station_seq`), and the known delay there.
2. `eta_service.model_based_eta()` loads the trained bundle via
   `app/ml/model_loader.py`.
3. `model_loader.predict_with_gbm()` rebuilds the exact feature vector
   used at training time (see `ml/train_gbm_model.py::FEATURE_COLUMNS`)
   for every upcoming section on the route, and calls the P50/P90
   quantile models.
4. Backend returns a confidence band per upcoming station, not a single
   number — this is deliberate (see `docs/PROJECT_BRIEF.md` §4).
5. Falls back to `naive_baseline_eta()` automatically if no trained model
   file exists yet, so the endpoint never hard-fails during development.

## Data flow for the "live" demo

1. Frontend opens an `EventSource` against `GET /api/live/{train_no}/stream`.
2. Backend's `live_feed_service.py` imports `live_feed_simulator.py` from
   the dataset package and streams its `departure`/`position`/`arrival`
   events as Server-Sent Events, at an accelerated playback speed.
3. This is a **stand-in for a real RTIS/COA feed**. The interface
   (position pings with lat/lon, speed, timestamp) is intentionally shaped
   like what a real feed would look like, so swapping the source later
   means changing `live_feed_service.py`, not the frontend or the ETA
   model's feature contract.

## Roles

| Role | Can do |
|---|---|
| Public (no login) | Browse trains, view schedules, request ETA predictions |
| Staff | Same as public today — TODO(Antigravity): add a control-room dashboard view (multiple trains at once, delay heatmap) as the staff-specific value-add |
| Admin | Everything above + Train Master CRUD (`/api/admin/trains`) |

Auth is currently two hardcoded demo accounts (`admin`/`admin123`,
`staff`/`staff123`) returning static tokens — see
`backend/app/core/security.py` and `backend/app/api/routes/auth.py` for
the TODO on replacing this with real JWT + a Users table.

## What's real vs. what's a stub — quick reference

| Piece | Status |
|---|---|
| Public train browse/detail | ✅ working, reads real CSVs |
| Naive baseline ETA | ✅ working |
| ML-backed ETA (P50/P90) | ✅ working — trained model wired in |
| Live SSE simulation | ✅ working |
| Admin Train Master CRUD | ✅ working, but **in-memory only** — resets on restart |
| Admin/staff auth | ⚠️ demo-only static tokens, not real auth |
| Persistent database | ❌ not built — see `data_store.py` TODOs |
| Frontend visual design | ❌ placeholder markup only — Stitch UI drops in here |
| Autoregressive multi-step ML chaining | ⚠️ approximated — see TODO in `model_loader.py` |
