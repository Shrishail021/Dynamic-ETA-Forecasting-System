#!/usr/bin/env python3
"""
Generate a synthetic-but-calibrated historical training dataset for the
dynamic ETA forecasting model (SIH PS 26028).

Outputs (in ./data/):
  stations.csv             - station master (code, name, lat, lon)
  sections.csv              - static per-section characteristics
  trains.csv                 - train master
  schedule.csv               - per-train, per-station scheduled times
  historical_journeys.csv    - the main ML training table (one row per
                                train x date x station-stop)

Usage:
  python3 generate_historical_dataset.py --days 240 --seed 42

Increase --days to generate more training data. Each additional day adds
roughly (number of trains that run that day) x (stops per route) rows.
"""

import argparse
import csv
import random
from datetime import date, datetime, timedelta

from railway_sim.network import STATIONS, SECTIONS, TRAINS, sections_for_route
from railway_sim.schedule import build_train_schedule, ORIGIN_DEPARTURE_TIME
from railway_sim.dynamics import simulate_section, season_of, is_festival_season


def write_static_tables():
    with open("data/stations.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["station_code", "station_name", "latitude", "longitude"])
        for s in STATIONS.values():
            w.writerow([s.code, s.name, s.lat, s.lon])

    with open("data/sections.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["route_id", "seq", "from_code", "to_code", "distance_km",
                     "scheduled_min", "scheduled_avg_speed_kmph",
                     "permissible_speed_kmph", "terrain",
                     "fog_prone", "congestion_level", "halt_min_at_to"])
        for s in SECTIONS:
            sched_speed = round(s.distance_km / (s.scheduled_min / 60.0), 1)
            w.writerow([s.route_id, s.seq, s.from_code, s.to_code, s.distance_km,
                        s.scheduled_min, sched_speed, s.permissible_speed_kmph,
                        s.terrain, s.fog_prone, s.congestion_level, s.halt_min_at_to])

    with open("data/trains.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["train_no", "train_name", "route_id", "train_type",
                     "priority", "recovery_fraction", "days_of_week",
                     "origin_departure_time"])
        for t in TRAINS:
            w.writerow([t.train_no, t.train_name, t.route_id, t.train_type,
                        t.priority, t.recovery_fraction,
                        "|".join(str(d) for d in t.days_of_week),
                        ORIGIN_DEPARTURE_TIME[t.train_no]])

    with open("data/schedule.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["train_no", "seq", "station_code", "distance_from_origin_km",
                     "scheduled_arrival_min", "scheduled_departure_min", "halt_min"])
        for t in TRAINS:
            for stop in build_train_schedule(t):
                w.writerow([t.train_no, stop["seq"], stop["station_code"],
                            stop["distance_from_origin_km"],
                            stop["scheduled_arrival_min"],
                            stop["scheduled_departure_min"], stop["halt_min"]])


def generate_journeys(num_days: int, start_date: date, seed: int):
    rng = random.Random(seed)
    rows = []

    for t in TRAINS:
        secs = sections_for_route(t.route_id)
        schedule = build_train_schedule(t)
        origin_time = ORIGIN_DEPARTURE_TIME[t.train_no]
        oh, om = map(int, origin_time.split(":"))

        for day_offset in range(num_days):
            journey_date = start_date + timedelta(days=day_offset)
            if journey_date.weekday() not in t.days_of_week:
                continue

            origin_dt = datetime(journey_date.year, journey_date.month, journey_date.day, oh, om)
            incoming_delay = 0.0
            rolling_delays = []
            prev_seq_delay = 0.0

            for i, sec in enumerate(secs):
                dep_dt = origin_dt + timedelta(minutes=schedule[i]["scheduled_departure_min"])
                outcome = simulate_section(rng, sec, t, journey_date, dep_dt, incoming_delay)

                stop = schedule[i + 1]
                rolling_delays.append(outcome["arrival_delay_min"])
                rolling_avg3 = sum(rolling_delays[-3:]) / len(rolling_delays[-3:])

                rows.append({
                    "train_no": t.train_no,
                    "train_name": t.train_name,
                    "route_id": t.route_id,
                    "train_type": t.train_type,
                    "priority": t.priority,
                    "journey_date": journey_date.isoformat(),
                    "day_of_week": journey_date.weekday(),
                    "month": journey_date.month,
                    "season": season_of(journey_date),
                    "is_festival_day": is_festival_season(journey_date),
                    "station_seq": stop["seq"],
                    "from_station": sec.from_code,
                    "to_station": sec.to_code,
                    "distance_from_origin_km": stop["distance_from_origin_km"],
                    "section_distance_km": sec.distance_km,
                    "scheduled_arrival_min_from_origin": stop["scheduled_arrival_min"],
                    "scheduled_departure_min_from_origin": stop["scheduled_departure_min"],
                    "halt_min_scheduled": sec.halt_min_at_to,
                    "section_permissible_speed_kmph": sec.permissible_speed_kmph,
                    "section_scheduled_avg_speed_kmph": outcome["scheduled_avg_speed_kmph"],
                    "fog_prone_section": sec.fog_prone,
                    "congestion_level_static": sec.congestion_level,
                    "departure_hour_of_day": dep_dt.hour,
                    "weather_condition": outcome["weather_condition"],
                    "visibility_m": outcome["visibility_m"],
                    "temperature_c": outcome["temperature_c"],
                    "is_tsr_event": outcome["is_tsr"],
                    "tsr_effective_speed_kmph": outcome["tsr_effective_speed_kmph"],
                    "prev_station_arrival_delay_min": round(prev_seq_delay, 1),
                    "rolling_avg_delay_last3_min": round(rolling_avg3, 1),
                    # --- outcome / target fields (see README: leakage note) ---
                    "arrival_delay_min": outcome["arrival_delay_min"],
                    "actual_running_min": outcome["actual_running_min"],
                    "section_avg_speed_kmph": outcome["avg_speed_kmph"],
                    "speed_anomaly_flag": outcome["speed_anomaly"],
                    "recovered_min": outcome["recovered_min"],
                })

                incoming_delay = outcome["arrival_delay_min"] + outcome["extra_halt_overstay_min"]
                prev_seq_delay = outcome["arrival_delay_min"]

    return rows


FIELDNAMES = [
    "train_no", "train_name", "route_id", "train_type", "priority",
    "journey_date", "day_of_week", "month", "season", "is_festival_day",
    "station_seq", "from_station", "to_station", "distance_from_origin_km",
    "section_distance_km", "scheduled_arrival_min_from_origin",
    "scheduled_departure_min_from_origin", "halt_min_scheduled",
    "section_permissible_speed_kmph", "section_scheduled_avg_speed_kmph", "fog_prone_section",
    "congestion_level_static", "departure_hour_of_day", "weather_condition",
    "visibility_m", "temperature_c", "is_tsr_event", "tsr_effective_speed_kmph",
    "prev_station_arrival_delay_min", "rolling_avg_delay_last3_min",
    "arrival_delay_min", "actual_running_min", "section_avg_speed_kmph",
    "speed_anomaly_flag", "recovered_min",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=240, help="number of calendar days to simulate")
    ap.add_argument("--start", type=str, default="2025-10-01", help="start date YYYY-MM-DD")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    start_date = datetime.strptime(args.start, "%Y-%m-%d").date()

    write_static_tables()
    rows = generate_journeys(args.days, start_date, args.seed)

    with open("data/historical_journeys.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to data/historical_journeys.csv "
          f"across {len(TRAINS)} trains, {args.days} days.")


if __name__ == "__main__":
    main()
