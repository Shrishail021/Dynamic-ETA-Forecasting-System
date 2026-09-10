# RailPulse — Application Portal, Dashboard Links & Model Training Guide
### Smart India Hackathon 2026 | PS 26028 | Ministry of Railways

This document provides direct links for every dashboard, one-click launcher commands, and complete instructions to train and benchmark **multiple machine learning models**.

---

## 1. Quick Launch (One-Click)

### Option A: Automatic Launcher (PowerShell)
Right-click or run from the repository root:
```powershell
.\start_railpulse.ps1
```
*(Starts the FastAPI backend on port `8000`, the Vite frontend on port `5173`, and automatically opens your browser)*

### Option B: Double-Click Batch File (Windows)
Double-click:
```
start_railpulse.bat
```

### Option C: Manual Launch (Two Terminals)
**Terminal 1 (Backend API):**
```powershell
cd backend
py -3.12 -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 (Frontend UI):**
```powershell
cd frontend
npm run dev
```

---

## 2. Direct Links to Every Dashboard & Interface

Click any of the links below once the app is running:

| Interface | Direct URL | Description | Required Role |
|---|---|---|---|
| **Home Radar Hub** | [http://localhost:5173/](http://localhost:5173/) | Landing hub, instant search bar, hot lookup chips, tracked corridors | Public (No login) |
| **Browse Trains Directory** | [http://localhost:5173/trains](http://localhost:5173/trains) | Responsive grid, corridor route and train type filters, live delay pills | Public (No login) |
| **Live ETA: 12302 Howrah Rajdhani** | [http://localhost:5173/trains/12302](http://localhost:5173/trains/12302) | Topology timeline, pulsing transit dot, P50/P90 confidence gauge, live SSE feed | Public (No login) |
| **Live ETA: 12951 Mumbai Rajdhani** | [http://localhost:5173/trains/12951](http://localhost:5173/trains/12951) | Live tracking, sectional speed telemetry, delay injector | Public (No login) |
| **Live ETA: 12007 Shatabdi** | [http://localhost:5173/trains/12007](http://localhost:5173/trains/12007) | Southern corridor live tracking (Bengaluru → Chennai) | Public (No login) |
| **Operations Control Room** | [http://localhost:5173/control-room](http://localhost:5173/control-room) | Multi-train matrix, network punctuality KPI, average delay, fog & congestion advisories | `staff` or `admin` |
| **Train Master Directory** | [http://localhost:5173/admin/trains](http://localhost:5173/admin/trains) | SQLite persistent CRUD table, "+ Register New Train" modal with auto-schedule derivation | `admin` |
| **Model Performance & Benchmarks** | [http://localhost:5173/admin/models](http://localhost:5173/admin/models) | Multi-model leaderboard comparison, P90 coverage gauge, download `.sql` dump | Public / Staff |
| **Staff & Admin Portal Login** | [http://localhost:5173/admin/login](http://localhost:5173/admin/login) | Terminal-styled login with 1-click credentials filler (`admin` or `staff`) | Public |
| **Interactive API Swagger Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive Swagger UI testing all REST and SSE endpoints | Any |
| **API Route Directory** | [http://localhost:8000/api](http://localhost:8000/api) | JSON index of all registered backend endpoints | Any |
| **Backend System Health** | [http://localhost:8000/api/health](http://localhost:8000/api/health) | Verifies SQLite database connection and ML model bundle status | Any |

---

## 3. Training & Benchmarking Multiple ML Models

RailPulse provides a multi-model benchmarking pipeline that evaluates **5 distinct regression architectures** on a chronological (80% train / 20% test) held-out dataset of over 9,000 journey records.

### How to Train All Models in One Command:
```powershell
cd ml
py -3.12 train_all_models.py
```

### Multiple Model Architectures & Empirical Results:

| Model Architecture | Algorithm Type | Mean Absolute Error (MAE) | Accuracy Gain | $R^2$ Score | Uncertainty Interval |
|---|---|---|---|---|---|
| **Random Forest Regressor** | Tree Bagging Ensemble (100 trees) | **4.10 min** | **+78.5%** | 0.970 | Estimator Variance |
| **HistGradientBoosting (Point)** | Gradient Boosted Decision Trees | **4.10 min** | **+78.5%** | 0.971 | Point Estimate |
| **HistGradientBoosting (Quantile P50/P90)** *(Primary RailPulse Engine)* | Quantile Gradient Boosted Regressor | **4.12 min** | **+78.4%** | 0.965 | **Yes (P90 Empirical Coverage: 86.1%)** |
| **Ridge Linear Regressor** | Regularized L2 Linear Model | **8.39 min** | **+56.1%** | 0.895 | Parametric Norm |
| **Naive Baseline (Current Railway Standard)** | Heuristic (Persistence + Buffer) | **19.11 min** | **0.0%** (Baseline) | 0.521 | None (Fixed 5m buffer) |

> [!IMPORTANT]
> **Why HistGradientBoosting Quantile is the Primary Engine:**
> While Random Forest and HGB Point achieve identical ~4.10 min MAE, the **Quantile Regressor** predicts dual P50 (median) and P90 (90th percentile) intervals. In real rail dispatching, knowing that a train *"will likely arrive in +15 min, but could be as late as +22 min"* is vastly more actionable for conflict resolution than a bare point estimate.

---

## 4. How to Train Individual Models

### 1. Train Primary Quantile GBM Model (P50 / P90):
```powershell
cd ml
py -3.12 train_gbm_model.py
```
*Outputs: `ml/models/eta_gbm_model.joblib` and `ml/models/gbm_metrics.json`.*

### 2. Train Naive Baseline Model:
```powershell
cd ml
py -3.12 train_baseline_model.py
```
*Outputs: `ml/models/baseline_metrics.json`.*

### 3. Retrain Models with Newly Captured Live Telemetry:
```powershell
cd ml
py -3.12 retrain_with_new_data.py
```
*Merges newly logged journey arrival telemetry from SQLite with the base historical dataset, fits fresh quantile models, and updates `ml/models/eta_gbm_model.joblib`.*

---

## 5. Future Prediction Data Store & SQL File Export

RailPulse records incoming live position pings and prediction requests into local storage so they can be reviewed, backed up, or used for model retraining:

- **Local Storage Path**: `backend/data/railpulse.db` (SQLite)
- **Database Tables**:
  - `journey_telemetry_log`: Logs timestamps, speeds, estimated delays, station codes, and raw JSON payloads from live simulation feeds.
  - `predictions_log`: Logs all P50/P90 dynamic predictions made by the system.
- **Exporting as a `.sql` File**:
  - Open `http://localhost:5173/admin/models` in your browser and click **"Download Telemetry SQL Dump"**.
  - Or download directly via API: `GET http://localhost:8000/api/telemetry/export.sql`
  - Output file: `backend/data/telemetry_export.sql`

---

## 6. Demo Accounts & Credentials

| Role | Username | Password | Capabilities |
|---|---|---|---|
| **Admin** | `admin` | `admin123` | Full control: Train Master CRUD, auto-schedule generator, model analytics, SQL exports |
| **Staff** | `staff` | `staff123` | Operations: Control Room multi-train matrix, telemetry counters, SQL exports |
| **Public** | *(No login)* | *(None)* | Public Radar, Train Search, Live Single-Train ETA & Simulation |

---

## 7. Interactive Features & Core Railway Problems Solved

### A. Route Topology Progression (Horizontal & Vertical Views)
On every live train tracking page (e.g. `http://localhost:5173/trains/12302`):
- **Horizontal Schematic View**: A subway/corridor style horizontal track diagram displaying all stops sequentially with glowing transit indicators, distance markers, delay tags, and platform designations.
- **Vertical Stepper Log**: A chronological station-by-station ledger showing scheduled arrival/departure, predicted arrival (P50/P90), dwell time, and speed limits.
- **Dynamic Adaptability**: When any train is selected or requested, the route topology immediately computes and dynamically re-renders stops, distances, and sectional properties for that specific train.

### B. Interactive Leaflet GIS Map
- Embedded Leaflet map powered by CartoDB Dark Voyager vector tiles.
- Dynamically parses station GPS coordinates (lat/long) for the selected train route.
- Renders glowing station marker pins with detailed schedule popups.
- Draws high-visibility route polylines reflecting train progression.
- Animates a live locomotive transit puck (`🚂`) indicating current sectional progress in real-time.
- Features smooth `AutoFitRoute` bounds transitions when switching between different trains.

### C. Browse by GPS Location (Nearest Station Finder)
- Available on both the **Home Radar Hub** (`/`) and **Coaching Train Radar** (`/trains`).
- Users can click **"Use My GPS Location"** to automatically acquire browser coordinates via `navigator.geolocation`.
- The backend executes a **Haversine Distance Algorithm** against all Indian Railways station coordinates stored in SQLite.
- Instantly identifies the nearest station (e.g., `NDLS`, `BCT`, `SBC`), computes exact distance in kilometers, and lists all trains stopping at or departing from that station.
- One-click test presets for major railway hubs (Delhi, Mumbai, Bengaluru) are included for instant demonstration.

### D. RailRadar Live API Ingestion Adapter
- **Endpoint**: `POST /api/live/railradar-adapter`
- Connects live GPS / NTES / RailRadar feeds directly to the dynamic ETA engine:
  ```json
  {
    "train_no": "12302",
    "timestamp": "2026-09-10T10:30:00Z",
    "current_lat": 27.18,
    "current_lon": 78.02,
    "speed_kmph": 72.5,
    "observed_delay_min": 14.0,
    "last_station_code": "CNB"
  }
  ```
- **Automated Delay Re-Forecasting**: Compares current speed against sectional maximum permissible speed (MPS) to detect Temporary Speed Restrictions (TSRs). Ingests telemetry into SQLite and immediately computes downstream P50 and P90 ETAs.
- Interactive modal available directly on the live tracking page (**"Feed RailRadar Live API"** button) to test custom delay scenarios.

---

## 8. Core Problems Solved by the RailPulse Engine

1. **Static Arithmetic vs Non-Linear Cascading Delays**:
   - *Problem*: Traditional systems compute ETA simply as `Remaining Distance / Average Speed`, failing to account for downstream priority overtakes, single-line clearance bottlenecks, and platform hold-ups.
   - *Solution*: RailPulse uses autoregressive Gradient Boosted Decision Trees trained on sectional historical features (hour of day, weather, rolling delay trend, train priority) to model compounding delays.

2. **False Precision vs Probabilistic Uncertainty (P50 / P90)**:
   - *Problem*: Giving a single deterministic ETA (e.g., "10:45 AM") leads to passenger frustration when disruptions occur.
   - *Solution*: Dual-quantile regression provides **P50** (most probable arrival) and **P90** (90% confidence upper bound buffer), giving section controllers and passengers actionable risk boundaries.

3. **Speed Restriction & Block Anomaly Detection**:
   - *Problem*: Unexpected track maintenance, TSRs, or locomotive deceleration cause silent delay propagation.
   - *Solution*: Real-time telemetry ingestion identifies speed deficits below section limits and flags anomalies before cascading into downstream blocks.

4. **Continuous Learning & Data Retention**:
   - *Problem*: Static schedule lookup tables degrade over time as operational conditions drift.
   - *Solution*: All live updates, delay observations, and predictions are stored in `railpulse.db` with one-click `.sql` export and automated model retraining scripts (`retrain_with_new_data.py`).
