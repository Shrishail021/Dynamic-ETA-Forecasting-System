"""
Script to seed all 103 real Indian Railways trains from
synthetic_training_dataset_FINAL_clean.csv into SQLite (railpulse.db)
and CSVs so that any train can be searched, browsed, and tracked with real-time ETA.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

DATA_FILE = Path("data/railway_eta_dataset/data/synthetic_training_dataset_FINAL_clean.csv")
DB_PATH = Path("backend/data/railpulse.db")

def seed():
    print(f"Loading {DATA_FILE}...")
    df = pd.read_csv(DATA_FILE)
    print(f"Total rows: {len(df):,}")

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # Check if platform_no column exists in schedule table, if not add it
    cur.execute("PRAGMA table_info(schedule)")
    cols = [r[1] for r in cur.fetchall()]
    if "platform_no" not in cols:
        cur.execute("ALTER TABLE schedule ADD COLUMN platform_no TEXT DEFAULT 'PF-1'")
        conn.commit()

    # 1. Stations
    print("Extracting unique stations...")
    st_df = df.drop_duplicates(subset=["station_code"])[["station_code", "station_name", "lat", "lon"]]
    stations_inserted = 0
    for _, s in st_df.iterrows():
        cur.execute("""
            INSERT OR REPLACE INTO stations (station_code, station_name, state, latitude, longitude)
            VALUES (?, ?, ?, ?, ?)
        """, (str(s["station_code"]).strip().upper(), str(s["station_name"]).strip(), "Indian Railways", float(s["lat"]), float(s["lon"])))
        stations_inserted += 1
    print(f"Inserted/updated {stations_inserted} stations.")

    # 2. Extract Trains and Schedules
    print("Extracting trains and schedules for all 103 trains...")
    unique_train_nos = df["train_no"].unique()
    trains_count = 0
    schedules_count = 0

    for t_no in unique_train_nos:
        t_rows = df[df["train_no"] == t_no].drop_duplicates(subset=["seq"]).sort_values("seq")
        if t_rows.empty:
            continue

        first_row = t_rows.iloc[0]
        train_no_str = str(t_no).strip()
        train_name = str(first_row.get("train_name", f"Express {train_no_str}"))

        # Determine train type & priority
        name_lower = train_name.lower()
        if any(x in name_lower for x in ["rajdhani", "shatabdi", "vande", "tejas", "duronto"]):
            train_type = "rajdhani_shatabdi_vb"
            priority = 1
            default_pf = 1
        elif any(x in name_lower for x in ["superfast", "sf ", "mail"]):
            train_type = "superfast"
            priority = 2
            default_pf = 2
        elif any(x in name_lower for x in ["passenger", "memu", "suburban"]):
            train_type = "passenger"
            priority = 4
            default_pf = 4
        else:
            train_type = "express"
            priority = 3
            default_pf = 3

        # Parse origin departure time
        sched_dep_str = str(first_row.get("scheduled_departure", "08:00:00"))
        try:
            dep_parts = sched_dep_str.split(":")
            origin_dep_clock = f"{int(dep_parts[0]):02d}:{int(dep_parts[1]):02d}"
            base_minutes = int(dep_parts[0]) * 60 + int(dep_parts[1])
        except Exception:
            origin_dep_clock = "08:00"
            base_minutes = 480

        route_id = f"R{priority}_{first_row['station_code']}_{t_rows.iloc[-1]['station_code']}"

        # Insert into trains
        cur.execute("""
            INSERT OR REPLACE INTO trains (train_no, train_name, route_id, train_type, priority, recovery_fraction, days_of_week, origin_departure_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (train_no_str, train_name, route_id, train_type, priority, 0.10, "0|1|2|3|4|5|6", origin_dep_clock))
        trains_count += 1

        # Delete old schedule for this train if re-seeding
        cur.execute("DELETE FROM schedule WHERE train_no = ?", (train_no_str,))

        # Insert each stop in schedule
        for idx, (_, stop) in enumerate(t_rows.iterrows()):
            seq = int(stop["seq"])
            st_code = str(stop["station_code"]).strip().upper()
            dist_km = float(stop.get("distance_km", 0.0))

            # Parse arrival & departure minutes from origin
            arr_str = str(stop.get("scheduled_arrival", sched_dep_str))
            dep_str = str(stop.get("scheduled_departure", sched_dep_str))

            def parse_mins(s):
                try:
                    p = s.split(":")
                    return int(p[0]) * 60 + int(p[1])
                except Exception:
                    return base_minutes

            arr_m = parse_mins(arr_str)
            dep_m = parse_mins(dep_str)

            # Cumulative minutes from origin
            if arr_m < base_minutes:
                # Crossed midnight
                arr_offset = (arr_m + 1440) - base_minutes
            else:
                arr_offset = arr_m - base_minutes

            if dep_m < base_minutes:
                dep_offset = (dep_m + 1440) - base_minutes
            else:
                dep_offset = dep_m - base_minutes

            # Ensure monotonic offsets
            if idx > 0 and arr_offset < idx * 15:
                arr_offset = idx * 35
                dep_offset = arr_offset + 2

            halt_min = max(1.0, float(dep_offset - arr_offset))
            if idx == 0:
                arr_offset = 0.0
                halt_min = 0.0

            # Assign realistic platform number based on train priority and stop sequence
            pf_num = ((default_pf + seq) % 4) + 1
            pf_str = f"Platform {pf_num}"

            cur.execute("""
                INSERT INTO schedule (train_no, seq, station_code, distance_from_origin_km, scheduled_arrival_min, scheduled_departure_min, halt_min, platform_no)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (train_no_str, seq, st_code, dist_km, float(arr_offset), float(dep_offset), float(halt_min), pf_str))
            schedules_count += 1

    conn.commit()
    conn.close()

    print(f"Seeding Complete!")
    print(f"Total Trains in Database: {trains_count}")
    print(f"Total Schedule Stops: {schedules_count}")

if __name__ == "__main__":
    seed()
