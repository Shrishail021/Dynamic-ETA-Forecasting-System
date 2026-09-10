# Stitch UI Prompt(s) — Dynamic ETA Forecasting System

Stitch generates one screen well per prompt. Use the **overview block**
below to set context once (paste it first if Stitch supports a
project-level brief), then paste each **screen prompt** one at a time.

---

## Overview / design brief (paste first)

```
App: "RailPulse" — a dynamic ETA forecasting system for Indian Railways
coaching trains (Smart India Hackathon prototype, Ministry of Railways
theme).

Design direction: modern, futuristic transit-dashboard aesthetic —
think real-time flight-tracker apps crossed with a control-room display.
Dark theme as the primary mode. Deep navy/near-black background
(#0b0f14), glassmorphism cards with subtle blur and a thin glowing
border, an electric cyan/blue accent (#33c2ff) for live/active elements,
amber (#ffb020) for delay warnings, and coral-red (#ff5470) reserved for
severe delay/critical states only. Clean geometric sans-serif type
(Inter or Space Grotesk). Generous spacing, rounded-corner cards (12-16px
radius), subtle motion cues implied in the design (a pulsing dot for
"live", a thin animated progress line for a train in transit).

Iconography: minimal line icons, rail/transit themed (train, station pin,
clock, speedometer, cloud/fog, map pin) — not literal photographic
imagery.

This is a functioning prototype with a working backend; every screen
below needs to accommodate REAL dynamic data (variable-length lists,
numbers that can be large or zero, an explicit "simulated data" disclaimer
that must remain visible, not decorative filler text).

Responsive: design for both a desktop dashboard layout and a mobile
single-column layout — most public/passenger users will be on mobile.
```

---

## Screen 1 — Home / Search

```
A landing screen for a train ETA app. Prominent search bar at the top
("Search train number, name, or station"). Below it, a "Popular / recent
trains" horizontal scroll of train cards (train number, name, type badge
like "Rajdhani" or "Express", small live-status dot). Below that, a
simple 3-step "How it works" strip (Search → Track → Get live ETA) with
icons. A route-map illustration or abstract line-art of India with route
lines as a subtle background element, not the focal point. Footer includes
a small, legible disclaimer: "Prototype system running on simulated data
— not real Indian Railways operational data."
```

## Screen 2 — Browse / Search Results

```
A browse screen listing trains as cards in a responsive grid (1 column
mobile, 3 columns desktop). Each card shows: train number + name, a route
badge (origin → destination station codes), a train-type pill (Rajdhani /
Superfast / Express / Passenger, each a distinct subtle color), and a
live-status indicator (a small colored dot + text: "On time" green,
"Delayed Xm" amber, "Severely delayed" red). A filter bar above the grid
with dropdowns for Route and Train Type. Empty state design for "no
trains match" case.
```

## Screen 3 — Live ETA (the core screen)

```
A single train's live tracking screen. Header: train number, name, and
type badge. Below it, a horizontal route timeline showing every station
as a dot on a line, with the train's current position marked with a
pulsing glowing dot between two stations. Completed stations are filled/
solid, upcoming stations are outlined. Below the timeline, a prominent
"Next station" card: station name, a large ETA time, and a visual
confidence band — a horizontal gradient bar or gauge showing the P50
estimate as a solid marker and the P90 estimate as a lighter shaded
range extending past it (label it plainly: "Likely arrival" for P50,
"Could be as late as" for P90 — do not make this look like a single
certain number). A secondary row of small stat chips: current delay,
weather condition icon, "speed anomaly detected" warning chip (only shown
when true, amber/red). Below that, a scrollable list of all upcoming
stations with their own smaller ETA + confidence range. A live indicator
badge (pulsing dot + "LIVE SIMULATION" text) somewhere near the top,
distinct from the disclaimer footer — this must not be confused with a
claim of a real live feed.
```

## Screen 4 — Admin Login

```
A clean, minimal login screen for staff/admin — centered card on a dark
background with the app's rail-themed logo mark above it, username and
password fields, a "Log in" button in the accent cyan, and a small note
below the form distinguishing "Admin" and "Staff" access levels. Nothing
public-facing or flashy — this should read as a utility/back-office
screen, deliberately calmer than the passenger-facing screens.
```

## Screen 5 — Train Master (Admin)

```
An admin data-management screen: a data table of trains (columns: Train
No, Name, Route, Type, Priority, actions). A prominent "+ Add Train"
button opens a modal/side-panel form with fields for train number, name,
route (dropdown), type (dropdown), priority, recovery fraction, running
days (day-of-week toggle chips), and origin departure time. Table rows
have inline edit/delete icon buttons. Include a small banner/callout at
the top of the page noting this is Train Master data used to generate
schedules and ETA predictions — changes take effect immediately. Design
language should feel like a professional admin dashboard (dense,
scannable, data-forward) rather than the more expressive passenger
screens — but keep the same dark theme and accent color for consistency.
```

## Screen 6 — Model Performance (Admin, optional/stretch)

```
An admin analytics screen comparing the naive baseline method against the
ML model: two large stat cards side by side ("Naive baseline: ~19 min
MAE" vs "ML model: ~4 min MAE"), a simple bar or line chart comparing
error by train type or route, and a P90 band "coverage" indicator (a
simple gauge showing ~86% against a 90% target line). Include a visible
caption/footnote area for an honesty caveat about the numbers being from
a synthetic dataset — leave clear space for a 1-2 line disclaimer text
under the headline stats, don't design it as fine print that gets hidden.
```

---

## After generating

Export the components/CSS Stitch gives you and hand them to Antigravity
along with `docs/MASTER_PROMPT_ANTIGRAVITY.md` — task 3 in that prompt
tells Antigravity exactly which existing files to slot each screen's
output into (`frontend/src/pages/...`, `frontend/src/components/...`)
without breaking the data-fetching wiring already in place.
