# RailPulse — Dynamic ETA Forecasting System (SIH PS 26028)

A prototype for the Ministry of Railways problem statement on dynamic ETA
forecasting for coaching trains. **This is a foundation, not a finished
app** — the backend runs, the ML model is trained and wired in, and the
frontend builds and routes correctly, but the visual design is
intentionally unstyled (that comes from Stitch) and several pieces are
explicitly stubbed for completion in Antigravity. See
`docs/ARCHITECTURE.md`'s "what's real vs. what's a stub" table for the
exact current state.

## Start here

1. Read `docs/PROJECT_BRIEF.md` — the problem, the data-availability
   reality in India, and the honest feasibility assessment.
2. Read `docs/ARCHITECTURE.md` — how the pieces fit together and what's
   already working.

## Run it locally right now (before Antigravity touches anything)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/docs for the interactive API explorer

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

Demo admin login: `admin` / `admin123`. Demo staff login: `staff` /
`staff123`.

The dataset is already included at `data/railway_eta_dataset/` and the
trained model at `ml/models/eta_gbm_model.joblib` — nothing else to
generate before running the above.

## Regenerating or scaling the data / model

```bash
cd data/railway_eta_dataset
python3 generate_historical_dataset.py --days 400   # more training rows

cd ../../ml
python3 train_baseline_model.py
python3 train_gbm_model.py                            # retrains + re-saves the model
```

## Project layout

```
railway-eta-system/
├── docs/                         ← read these first
│   ├── ARCHITECTURE.md  
│  
├── data/railway_eta_dataset/      ← synthetic dataset + live simulator (already generated)
├── ml/                            ← training scripts + trained model
├── backend/                       ← FastAPI app (runs today)
└── frontend/                      ← Vite + React app (builds today, no visual design yet)
```

## The one thing to never let slip in the demo

Every page must keep visible that this runs on **simulated/prototype
data**, not real Indian Railways feeds. That's not a legal disclaimer —
it's what makes the "honest feasibility" framing in the project brief
credible to judges instead of looking like an overclaim. `Footer.jsx` has
this today; keep it (or an equivalent) through every UI iteration.
