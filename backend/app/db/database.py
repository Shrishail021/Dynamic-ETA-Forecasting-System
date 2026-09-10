"""
SQLite Persistence layer for RailPulse.
Handles schema creation, initial CSV seeding, thread-safe connections,
and tables for trains, stations, sections, schedules, users, and telemetry logs.
"""

import sqlite3
import hashlib
import os
from pathlib import Path
from typing import Optional
import pandas as pd
from app.core.config import settings

# Ensure DB folder exists
settings.DB_DIR.mkdir(parents=True, exist_ok=True)


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.DATABASE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str, salt: Optional[str] = None) -> str:
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    if ":" not in stored_hash:
        # Fallback for plain legacy passwords if any
        return plain_password == stored_hash
    salt, original_hash = stored_hash.split(":", 1)
    return hashlib.sha256((salt + plain_password).encode("utf-8")).hexdigest() == original_hash


def init_db():
    """Initializes schema and seeds from CSV if first run."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Trains table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trains (
                train_no TEXT PRIMARY KEY,
                train_name TEXT NOT NULL,
                route_id TEXT NOT NULL,
                train_type TEXT NOT NULL,
                priority INTEGER NOT NULL,
                recovery_fraction REAL NOT NULL,
                days_of_week TEXT NOT NULL,
                origin_departure_time TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Stations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stations (
                station_code TEXT PRIMARY KEY,
                station_name TEXT NOT NULL,
                state TEXT,
                latitude REAL,
                longitude REAL
            )
        """)

        # 3. Sections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id TEXT NOT NULL,
                seq INTEGER NOT NULL,
                from_code TEXT NOT NULL,
                to_code TEXT NOT NULL,
                distance_km REAL NOT NULL,
                permissible_speed_kmph REAL NOT NULL,
                scheduled_avg_speed_kmph REAL NOT NULL,
                halt_min_at_to REAL NOT NULL,
                fog_prone INTEGER NOT NULL,
                congestion_level REAL NOT NULL
            )
        """)

        # 4. Schedules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                train_no TEXT NOT NULL,
                seq INTEGER NOT NULL,
                station_code TEXT NOT NULL,
                distance_from_origin_km REAL NOT NULL,
                scheduled_arrival_min REAL NOT NULL,
                scheduled_departure_min REAL NOT NULL,
                halt_min REAL NOT NULL,
                FOREIGN KEY (train_no) REFERENCES trains(train_no) ON DELETE CASCADE
            )
        """)

        # 5. Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 6. Predictions Log (for offline model evaluation & training dataset augmentation)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                train_no TEXT NOT NULL,
                station_seq INTEGER NOT NULL,
                current_delay_min REAL NOT NULL,
                to_station TEXT NOT NULL,
                p50_delay_min REAL NOT NULL,
                p90_delay_min REAL NOT NULL,
                method TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 7. Journey Telemetry Log (for storing live telemetry pings for future prediction)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS journey_telemetry_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                train_no TEXT NOT NULL,
                journey_date TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TEXT,
                station_code TEXT,
                current_speed_kmph REAL,
                estimated_delay_so_far_min REAL,
                actual_delay_min REAL,
                raw_payload TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

        # Seed data if empty
        _seed_users(conn)
        _seed_from_csv(conn)


def _seed_users(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_hash = hash_password("admin123")
        staff_hash = hash_password("staff123")
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", admin_hash, "admin"))
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("staff", staff_hash, "staff"))
        conn.commit()


def _seed_from_csv(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM trains")
    trains_count = cursor.fetchone()[0]

    if trains_count > 0:
        return  # Already seeded

    data_dir = settings.DATA_DIR
    if not data_dir.exists():
        return

    # Seed Stations
    stations_file = data_dir / "stations.csv"
    if stations_file.exists():
        df_stations = pd.read_csv(stations_file)
        for _, row in df_stations.iterrows():
            cursor.execute("""
                INSERT OR IGNORE INTO stations (station_code, station_name, state, latitude, longitude)
                VALUES (?, ?, ?, ?, ?)
            """, (
                str(row.get("station_code", "")),
                str(row.get("station_name", "")),
                str(row.get("state", "")),
                float(row["latitude"]) if "latitude" in row and pd.notnull(row["latitude"]) else None,
                float(row["longitude"]) if "longitude" in row and pd.notnull(row["longitude"]) else None,
            ))

    # Seed Sections
    sections_file = data_dir / "sections.csv"
    if sections_file.exists():
        df_sections = pd.read_csv(sections_file)
        for _, row in df_sections.iterrows():
            cursor.execute("""
                INSERT INTO sections (route_id, seq, from_code, to_code, distance_km,
                                      permissible_speed_kmph, scheduled_avg_speed_kmph,
                                      halt_min_at_to, fog_prone, congestion_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row["route_id"]),
                int(row["seq"]),
                str(row["from_code"]),
                str(row["to_code"]),
                float(row["distance_km"]),
                float(row["permissible_speed_kmph"]),
                float(row["scheduled_avg_speed_kmph"]),
                float(row["halt_min_at_to"]),
                1 if bool(row["fog_prone"]) else 0,
                float(row["congestion_level"]),
            ))

    # Seed Trains
    trains_file = data_dir / "trains.csv"
    if trains_file.exists():
        df_trains = pd.read_csv(trains_file, dtype={"train_no": str})
        for _, row in df_trains.iterrows():
            cursor.execute("""
                INSERT OR REPLACE INTO trains (train_no, train_name, route_id, train_type,
                                              priority, recovery_fraction, days_of_week,
                                              origin_departure_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row["train_no"]),
                str(row["train_name"]),
                str(row["route_id"]),
                str(row["train_type"]),
                int(row["priority"]),
                float(row["recovery_fraction"]),
                str(row["days_of_week"]),
                str(row["origin_departure_time"]),
            ))

    # Seed Schedule
    schedule_file = data_dir / "schedule.csv"
    if schedule_file.exists():
        df_schedule = pd.read_csv(schedule_file, dtype={"train_no": str})
        for _, row in df_schedule.iterrows():
            cursor.execute("""
                INSERT INTO schedule (train_no, seq, station_code, distance_from_origin_km,
                                      scheduled_arrival_min, scheduled_departure_min, halt_min)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row["train_no"]),
                int(row["seq"]),
                str(row["station_code"]),
                float(row["distance_from_origin_km"]),
                float(row["scheduled_arrival_min"]),
                float(row["scheduled_departure_min"]),
                float(row["halt_min"]),
            ))

    conn.commit()
