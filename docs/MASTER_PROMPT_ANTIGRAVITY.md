# Master Build Prompt — paste this into Antigravity

Copy everything below the line into Antigravity as your starting instruction, inside this project folder (`railway-eta-system/`).

---

You are working inside an existing project called **railway-eta-system**, a
prototype Dynamic ETA Forecasting System for Indian Railways coaching
trains (Smart India Hackathon, Problem Statement 26028, Ministry of
Railways). **Do not restructure the existing folders or rewrite working
code from scratch — extend and complete what's already here.** Read
`docs/ARCHITECTURE.md` and `docs/PROJECT_BRIEF.md` first for full context.

## What already exists and already works (verified — don't rebuild these)

- **`data/railway_eta_dataset/`** — a calibrated synthetic dataset
  generator and live GPS-ping simulator. `railway_sim/dynamics.py` is the
  shared "physics" both the historical CSV and the live simulator are
  built from. `data/historical_journeys.csv` has ~9,000 rows already
  generated. Read its `README.md` before touching feature engineering —
  it documents exactly which columns are safe pre-outcome features vs.
  which describe the outcome (leakage warning).
- **`ml/train_baseline_model.py`** and **`ml/train_gbm_model.py`** —
  already implemented and tested. They train P50/P90
  `HistGradientBoostingRegressor` quantile models and save them to
  `ml/models/eta_gbm_model.joblib`. Current results: naive baseline MAE
  ~19 min, GBM P50 MAE ~4 min. **Read `ml/README.md`'s caveat about this
  improvement number before presenting it anywhere** — it's inflated by
  clean synthetic data and needs to be framed carefully.
- **`backend/app/`** — a FastAPI app that runs today. Working endpoints:
  `GET /api/trains`, `GET /api/trains/{train_no}`,
  `POST /api/eta/predict` (real ML model wired in, with automatic
  fallback to the naive baseline), `GET /api/live/{train_no}/stream`
  (SSE), `POST /api/auth/login` (demo tokens), and full CRUD at
  `/api/admin/trains` (in-memory only — see persistence task below).
- **`frontend/`** — a Vite + React app that builds and runs, with routing
  already wired to every backend endpoint above. **The UI has zero visual
  design right now** — pages are unstyled raw HTML elements. This is
  intentional: visual design comes from Stitch (see
  `docs/STITCH_UI_PROMPT.md`), your job is to wire Stitch's output into
  the existing page components without breaking their data flow.

Every file with a `TODO(Antigravity)` comment is a specific, scoped task
left for you — grep for `TODO(Antigravity)` across the repo as your task
list before inventing new work.

## Your tasks, roughly in priority order

1. **Persistence.** Replace `backend/app/services/data_store.py`'s
   in-memory pandas DataFrames with SQLite (simplest: SQLModel or raw
   sqlite3), seeded once from the existing CSVs on first run. Admin
   create/update/delete in `admin_trains.py` currently mutates a
   DataFrame that resets on restart — fix that here.
2. **Real auth.** Replace the static demo tokens in
   `app/core/security.py` and `app/api/routes/auth.py` with a real Users
   table (hashed passwords) and signed JWTs. Keep the three roles:
   `public` (no login needed), `staff`, `admin`.
3. **Integrate the Stitch UI.** Take the screens generated from
   `docs/STITCH_UI_PROMPT.md` and wire them into the existing page files
   under `frontend/src/pages/` and `frontend/src/components/` — every
   placeholder component has a `TODO(Antigravity/Stitch)` comment naming
   exactly what to preserve (the data-fetching calls, the routing
   targets). Do not let new UI code fetch data directly with `fetch()` —
   route everything through `frontend/src/api/client.js`.
4. **Live re-forecasting.** Right now `GET /api/live/{train_no}/stream`
   streams the simulator's ground-truth outcome events; it does not
   re-run the ETA model on each position ping. Change
   `backend/app/api/routes/live.py`'s event generator so that on each
   `position` event, it calls `eta_service.model_based_eta()` using that
   event's `estimated_delay_so_far_min`, and includes the freshly
   re-forecast ETA in the SSE payload. This is the actual "dynamic"
   re-forecasting the problem statement asks for — don't skip it.
5. **Control-room / staff dashboard.** Currently `staff` role has no
   distinct capability from `public`. Add a dashboard view (new backend
   endpoint aggregating multiple trains' current delay + next-station ETA
   at once; new frontend page) as the staff-specific value — this maps
   directly to the problem statement's "control room dashboards" bullet.
6. **New-train schedule generation.** `admin_trains.py::create_train` has
   a TODO: a newly created train has no corresponding rows in
   `schedule.csv`/the schedule table. Add a form/flow (admin side) to
   define a train's stops (station, distance, scheduled times, halt) when
   creating it, and persist that alongside the train record.
7. **Autoregressive ML chaining (polish, do this last).**
   `backend/app/ml/model_loader.py::predict_with_gbm` has a documented
   approximation: it doesn't feed each section's prediction into the next
   section's `prev_station_arrival_delay_min`/`rolling_avg_delay_last3_min`
   within a single request. Rebuild the feature rows one at a time inside
   the loop instead of batching, chaining predictions forward.

## Hard constraints — do not violate these

- **Never claim the dataset or predictions are real Indian Railways
  data anywhere in UI copy, error messages, or docs.** Every page must
  keep some form of the disclaimer currently in `Footer.jsx` visible.
  This is a synthetic/prototype system and the SIH judges need to see
  that stated plainly, not discover it.
- **Do not feed outcome/post-hoc columns into the ETA model as input
  features.** The leakage-safe column list is documented in
  `data/railway_eta_dataset/README.md` and mirrored in
  `ml/train_gbm_model.py::FEATURE_COLUMNS`. If you retrain the model with
  new features, update both places and re-read the leakage section first.
- **Do not put the ~79% MAE-improvement figure in front of judges without
  the caveat in `ml/README.md`.** Cite the peer-reviewed real-data
  benchmark (13–15% improvement, RSTGCN, arXiv 2510.01262) as the honest
  comparison point instead.
- **Do not hardcode secrets.** Use the `.env.example` files already
  present in `backend/` and `frontend/` as the template for real `.env`
  files (gitignored).
- **Keep the existing API contract stable** (`/api/trains`,
  `/api/eta/predict`, `/api/live/{train_no}/stream`,
  `/api/admin/trains`) unless a task above explicitly asks you to change
  it — the frontend and the docs both depend on these exact shapes.

## Tech stack (fixed — do not swap without a strong reason)

- Backend: FastAPI, Python 3.12, pandas → SQLite for persistence,
  scikit-learn for ML (already trained; swap to XGBoost/LightGBM later
  only if you have a concrete reason)
- Frontend: React + Vite, React Router, plain fetch via
  `src/api/client.js` (no additional state-management library needed at
  this scale — don't add Redux/etc. unless the app genuinely outgrows
  Context)
- Styling: whatever Stitch exports (likely Tailwind or plain CSS) —
  integrate it, don't fight it with a second design system

## Acceptance criteria (how you'll know you're done)

- `cd backend && uvicorn app.main:app --reload` starts cleanly and
  `/api/health` returns `{"status": "ok"}`
- `cd frontend && npm run dev` starts cleanly and every route in
  `router.jsx` renders without console errors
- A judge can: open the app → search/browse trains → open a train → see
  a live-updating ETA with a visible confidence range while the live demo
  runs → log in as admin → add/edit a train in Train Master → see it
  reflected immediately in the public browse list
- Restarting the backend does NOT lose admin edits (persistence task
  done)
- No page anywhere implies this is real operational IR data
