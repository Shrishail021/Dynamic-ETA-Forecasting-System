# SIH 2026 — PS 26028: Dynamic ETA Forecasting for Coaching Trains

**Organization:** Ministry of Railways | **Category:** Software | **Theme:** Smart Automation

---

## 1. The Real Problem (stripped of jargon)

Today's ETA = scheduled time + current delay − a fixed recovery buffer. That's not a forecast, it's arithmetic on a static schedule. It doesn't know about:

- Temporary speed restrictions (TSRs) and fog (major cause of delay in North India winters)
- Whether this train is being held for a higher-priority train on a shared section
- Whether the timetable's "recovery time" is actually usable today given crew, loco, and traffic
- How delay compounds over a multi-day journey (small early delays cascade)

**Goal:** replace static extrapolation with a model that re-forecasts ETA at every station/checkpoint using real-time position + historical patterns + context (weather, day type, section characteristics).

---

## 2. Data Landscape in India — What's Actually Available

This determines the whole strategy, so get this right before writing any code.

| Data | Status | Notes |
|---|---|---|
| GPS train position (RTIS/REMMLOT) | Exists, not publicly exposed | ISRO-backed GPS on locomotives, ~30s update interval, feeds Control Office Application (COA) → NTES. ~50% of locos equipped as of 2023 (~14M position events/day). |
| NTES live status | Public via app/web, **no official API** | Unofficial scrapers/libraries exist (e.g. community Python clients); apps like RailRadar / "Where is my Train" run on scraped NTES/COA data. Hackathon teams realistically build on scraped historical data + a simulated live feed. |
| Historical punctuality / delay data | Public (data.gov.in, Ministry punctuality reports) | Use as training data for section-level delay models. |
| Weather | Public (IMD, data.gov.in) | Strong feature, especially fog belt routes in winter. |
| Static route data (timetables, sectional distances, permissible speeds) | Public (Working Time Tables, "Trains at a Glance") | Needed to build the per-section skeleton the model predicts over. |
| Signalling/interlocking occupancy, official TSR notices | **Not public** | Real gap. Workaround: infer TSR/congestion from GPS speed anomalies (train running below its historical normal speed on a known stretch) instead of requiring an official feed. |

**Key takeaway for the pitch:** be upfront that a hackathon prototype runs on historical/scraped/simulated data, with a clearly documented production path to direct COA/RTIS integration. This is normal and expected — judges know Railways won't hand a student team live control-room access.

---

## 3. Prior Art (so you're not reinventing, and can cite precedent)

Indian-context academic work already validates ML for this problem:
- Random Forest / Extra Trees / gradient boosting models on historical Indian Railways delay data, with real predictive value shown across multiple studies (2019–2025).
- At least one study specifically folds weather data into delay prediction for Indian Railways.
- International work (Netherlands, China, US) uses similar section-decomposition + ensemble regression approaches, and ensemble/graph-based models for station-level delay.

Use this in your submission — "beats a documented ML+domain baseline, not just the naive schedule method" is a much stronger claim than starting from zero.

---

## 4. Proposed Architecture

**Core idea:** don't predict "final ETA" directly. Decompose the journey into sections between consecutive stations, predict *next-section running time*, and re-forecast every time a new position update arrives.

```
[GPS/NTES feed] → [Feature pipeline] → [Section running-time model] → [Aggregate to destination]
                                                                              ↓
                                                          [Confidence band: P50/P90]
                                                                              ↓
                                        [API layer] → [Dashboard / mobile / station display]
```

**Section model features:**
- Scheduled arrival/departure at each station, distance, gradient/permissible speed of the segment
- Current delay + delay trend over the last 2–3 stations
- Day of week, festival/holiday calendar
- Weather (visibility, rain) for the section
- Historical average delay for this train number + section + time slot
- Derived "speed anomaly" signal (current speed vs. historical normal speed for that GPS segment) — proxy for TSR/congestion without needing an official feed
- Preceding train's delay/priority on shared sections, where inferable

**Model choice:** Gradient-boosted trees (XGBoost/LightGBM) as the primary regressor — matches what's worked in prior Indian Railways studies, trains fast, and is explainable. Consider quantile regression or conformal prediction to produce the P50/P90 band rather than a single point estimate — this materially increases trust in the output vs. a bare number.

**Serving layer:** simple REST/GraphQL API + a live dashboard (map view, per-station ETA, confidence band). For the hackathon, scale claims ("thousands of trains simultaneously") should be addressed as an architecture diagram (message queue + horizontally scalable model server), not something you need to actually load-test.

---

## 5. Honest Feasibility Assessment

- **Chance of a strong, judge-worthy prototype:** high. The data workaround is legitimate, the ML approach has direct academic precedent, and "beats naive schedule+recovery baseline by X minutes MAE on held-out historical routes" is a concrete, demoable result.
- **Chance of delivering the literal full expected solution** (live control-room integration, real congestion feeds, thousands of trains in production): not achievable in a hackathon timeframe, and not expected by judges. What's actually being scored is whether the architecture is real, the ML claim is validated on real data, and the demo is credible.
- **Competitive differentiation:** this PS is a recurring "Smart Automation" theme pick, so expect competition using generic delay-prediction tutorials. Stand out with (a) the TSR-via-speed-anomaly trick, (b) explicit fog/weather handling, and (c) uncertainty bands instead of a single point ETA.

---

## 6. Suggested Team Split (typical SIH team of 6)

1. **Data/backend** — build the historical dataset (scrape/collect NTES history + weather + timetable), build the simulated live-feed replayer
2. **ML** — section running-time model, baseline comparison, uncertainty quantification
3. **API** — serving layer, endpoints for dashboard/mobile/control-room use cases
4. **Frontend/dashboard** — map + live ETA view + confidence band UI
5–6. **Presentation/PPT + integration/testing**

---

## 7. Next Steps

1. Pick 5–10 routes/trains as your demo scope (mix of a fog-belt route and a congested-corridor route makes a good story)
2. Assemble historical data for those routes (delay history, timetable, weather)
3. Build the naive baseline (current railway method) first — you need this number to prove improvement against
4. Build the section model, validate MAE improvement over baseline
5. Wire up the live-look dashboard with a replay of historical data as a "simulated live feed"
6. Write the production-integration section of your PPT (how this plugs into real COA/RTIS/NTES) — this is what makes the judges believe it's real, not just a Kaggle exercise
