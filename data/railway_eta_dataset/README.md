# Synthetic ETA Dataset & Live Simulator — SIH PS 26028

## Why this exists

There is no downloadable public dataset that matches this problem exactly.
Indian Railways' real GPS/position feed (RTIS, via COA) is not publicly
exposed, and NTES has no official API. The closest real thing found during
research is a September 2025 academic paper (RSTGCN, arXiv 2510.01262)
that scraped a nationwide dataset from runningstatus.in — 3,892 trains,
4,735 stations — but that dataset is not publicly downloadable ("released
upon acceptance"). Its reported statistics were used below to calibrate
this synthetic dataset so it isn't just made-up numbers.

**This package generates its own dataset**, using one shared stochastic
model for both:
1. `data/historical_journeys.csv` — the training table for your ML model
2. `live_feed_simulator.py` — a "live" GPS-ping stream for demoing/testing
   your ETA-serving pipeline

Because both come from the same underlying model (`railway_sim/dynamics.py`),
a model trained on the historical CSV will behave sensibly against the live
stream — which is the actual point of building this instead of grabbing an
unrelated CSV off Kaggle.

## Quick start

```bash
# regenerate / scale up the training data (more days = more rows)
python3 generate_historical_dataset.py --days 240 --seed 42

# stream a live-look journey (prints JSON-lines, 120x playback speed)
python3 live_feed_simulator.py --train 12951 --date 2025-12-20 --speed 240

# or use it as a library
python3 -c "
from datetime import date
from live_feed_simulator import simulate_journey_events
for ev in simulate_journey_events('12951', date(2025,12,20), seed=7):
    print(ev)
"
```

Trains available: `12951 19269 12459 14673 12007 16021 12302 13005 56215 06231`
(see `data/trains.csv`). Routes cover a deliberately diverse set: a
Delhi–Mumbai trunk route, a Punjab fog-belt route, a South Indian
low-fog/monsoon route, a long-distance Howrah–Delhi trunk route, and a
short frequent-stop passenger corridor — matching the diversity the problem
statement calls out.

## ⚠️ Honesty about this data

Station coordinates, distances, and scheduled times are **approximate and
illustrative** — hand-assembled for prototyping, not sourced from the
official Working Time Table. They're good enough to build and demo a real
ML pipeline on, but say so explicitly in your SIH submission, and note that
a production version would swap this module for official IR master data
(WTT / NTES station master) and a real RTIS/COA feed. Judges will trust you
more for saying this plainly than for implying this is real operational
data.

## Calibration (so the delay distribution isn't arbitrary)

- Mean arrival delay in this dataset: ~54 minutes, close to the ~51-minute
  nationwide average reported in the RSTGCN paper (Sept 2024 data) and in
  the same ballpark as a 2023 industry punctuality analysis (~30 minutes,
  which weighted more short/urban routes).
- ~29% of arrivals exceed 60 minutes' delay in this dataset; a CAG audit
  cited in Indian press found roughly 21% of runs exceeded an hour late,
  across a broader, less congestion-skewed set of routes than the five
  modelled here.
- Premium trains (Rajdhani/Shatabdi-type) come out least delayed of the
  train types modelled, consistent with a 2023–24 industry analysis
  finding Vande Bharat/Shatabdi/Rajdhani trains have lower delays than
  other express categories.
- Fog is modelled as a winter-only, early-morning/late-night, fog-belt-only
  event that can add well over an hour — this matches the well-documented
  pattern of severe northern winter fog delays, and Ministry of Railways'
  own Parliament answers naming external factors (fog, law & order),
  congestion, asset failures, and infrastructure works as the four broad
  delay causes.
- Speed-restriction/congestion events are rare (~3.5% of sections) but
  large when they occur — meant to represent real TSRs and localized
  congestion, which are not publicly documented as live data feeds.

None of this should be read as "these are Indian Railways' real delay
statistics" — it's a deliberately-calibrated synthetic model. Treat the
generation logic in `railway_sim/dynamics.py` as the actual deliverable;
tune the constants there if you get access to better calibration data.

## Files

| File | What it is |
|---|---|
| `data/stations.csv` | Station code, name, approx lat/lon |
| `data/sections.csv` | Static per-section characteristics (distance, scheduled time, permissible speed, terrain, fog-proneness, congestion level) |
| `data/trains.csv` | Train master: type, priority, recovery fraction, running days, origin departure time |
| `data/schedule.csv` | Per-train, per-station scheduled arrival/departure (minutes from origin departure) and distance-from-origin |
| `data/historical_journeys.csv` | **Main ML training table** — one row per (train, date, station-stop) |
| `railway_sim/network.py` | Station/section/train static definitions — edit this to add routes |
| `railway_sim/dynamics.py` | The stochastic delay/weather/congestion/TSR model — the real "physics" |
| `railway_sim/schedule.py` | Builds per-train schedules from the section table |
| `generate_historical_dataset.py` | CLI: regenerate/scale the training CSV |
| `live_feed_simulator.py` | CLI + importable generator: streams a live-look journey |

## `historical_journeys.csv` schema, and a leakage warning

Columns fall into two groups:

**Known BEFORE the train departs the previous station** (safe to use as
model input features):
`train_no, train_name, route_id, train_type, priority, journey_date,
day_of_week, month, season, is_festival_day, station_seq, from_station,
to_station, distance_from_origin_km, section_distance_km,
scheduled_arrival_min_from_origin, scheduled_departure_min_from_origin,
halt_min_scheduled, section_permissible_speed_kmph,
section_scheduled_avg_speed_kmph, fog_prone_section,
congestion_level_static, departure_hour_of_day,
prev_station_arrival_delay_min, rolling_avg_delay_last3_min`

**Only known AFTER the section outcome happens** (these describe the
outcome itself — do NOT feed these into a model that's supposed to predict
the delay before it happens, or you'll get unrealistically good offline
metrics that fall apart in live use):
`weather_condition, visibility_m, temperature_c, is_tsr_event,
tsr_effective_speed_kmph, arrival_delay_min (TARGET), actual_running_min,
section_avg_speed_kmph, speed_anomaly_flag, recovered_min`

A defensible model formulation: predict `arrival_delay_min` using only the
"known before" columns plus a weather **forecast** (not the realized
weather) for that section/time. `speed_anomaly_flag` and
`section_avg_speed_kmph` are exactly the kind of signal your LIVE system
would compute in real time from the most recent GPS pings — they belong in
your **live re-forecasting** logic (recompute ETA once you see the anomaly
on the current section), not as an input to predict a delay that hasn't
happened yet.

`prev_station_arrival_delay_min` and `rolling_avg_delay_last3_min` are
safe: they're the outcome of *earlier* sections in the same journey, known
by the time you're forecasting the *next* one.

## `speed_anomaly_flag` — the TSR/congestion proxy

Since official TSR notices and live signalling occupancy aren't public,
the flag is defined as: **current section average speed < 65% of that
section's own scheduled average speed** (not the sanctioned top speed —
comparing to the ceiling would flag almost every normal run, since
schedules already run well below top speed for curves/gradients/halts).
In this dataset, sections flagged this way average ~83 minutes of delay
vs. ~48 minutes for non-flagged sections — i.e., it's a real, usable
signal, and it's exactly the kind of derived feature a live GPS-based
system can compute without needing an official TSR feed.

## Using `live_feed_simulator.py` for a demo

```bash
python3 live_feed_simulator.py --train 12302 --date 2025-01-15 --speed 300 --out sample_run.jsonl
```

This streams `departure` / `position` / `arrival` events for one full
journey. Point your ETA-serving code at this stream during development:
consume `position` events to recompute ETA as new "GPS" data arrives, and
compare your predictions against the `arrival` events' `delay_min` once
the train actually reaches each station. `--seed` makes a run
reproducible; omit it for a different random outcome each time.

## Scaling up

`--days N` in `generate_historical_dataset.py` linearly scales the
training set size (240 days ≈ 9,000 rows across the 10 trains modelled
here). To add more trains or routes, extend `_RAW_SECTIONS` and `TRAINS`
in `railway_sim/network.py` — the generator and simulator both pick up new
entries automatically.
