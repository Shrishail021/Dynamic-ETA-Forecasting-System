"""
Telemetry logging and persistence service.
Stores incoming live telemetry pings, departure/arrival events, and dynamic ETA
predictions into SQLite for audit, analytics, and future model retraining/fine-tuning.
Also provides SQL dump export capabilities as requested.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.db.database import get_db_connection
from app.core.config import settings


def log_prediction(train_no: str, station_seq: int, current_delay_min: float,
                   to_station: str, p50_delay_min: float, p90_delay_min: float, method: str):
    """Log individual station ETA prediction."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO predictions_log (train_no, station_seq, current_delay_min,
                                         to_station, p50_delay_min, p90_delay_min, method)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (str(train_no), int(station_seq), float(current_delay_min),
              str(to_station), float(p50_delay_min), float(p90_delay_min), str(method)))
        conn.commit()


def log_journey_event(train_no: str, journey_date: str, event_data: Dict[str, Any]):
    """Log live journey simulator or feed events."""
    event_type = event_data.get("event", "unknown")
    timestamp = event_data.get("timestamp") or event_data.get("actual_time") or datetime.now().isoformat()
    station_code = event_data.get("station") or event_data.get("from_station") or ""
    speed = float(event_data.get("speed_kmph", 0.0))
    est_delay = float(event_data.get("estimated_delay_so_far_min", 0.0))
    act_delay = float(event_data.get("arrival_delay_min", est_delay)) if "arrival_delay_min" in event_data else None

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO journey_telemetry_log (train_no, journey_date, event_type,
                                              timestamp, station_code, current_speed_kmph,
                                              estimated_delay_so_far_min, actual_delay_min, raw_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(train_no), str(journey_date), str(event_type), str(timestamp),
              str(station_code), speed, est_delay, act_delay, json.dumps(event_data)))
        conn.commit()


def get_telemetry_stats() -> Dict[str, Any]:
    """Returns count and summary of logged telemetry and predictions."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM journey_telemetry_log")
        telemetry_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM predictions_log")
        predictions_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT event_type, COUNT(*) as cnt
            FROM journey_telemetry_log
            GROUP BY event_type
        """)
        by_event = {row["event_type"]: row["cnt"] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT train_no, COUNT(*) as cnt
            FROM journey_telemetry_log
            GROUP BY train_no
            ORDER BY cnt DESC LIMIT 5
        """)
        top_trains = {row["train_no"]: row["cnt"] for row in cursor.fetchall()}

        return {
            "total_telemetry_records": telemetry_count,
            "total_predictions_logged": predictions_count,
            "breakdown_by_event": by_event,
            "top_logged_trains": top_trains,
        }


def export_telemetry_to_sql_file() -> str:
    """
    Exports all collected journey telemetry and predictions to a standalone .sql file.
    This fulfills the requirement of persisting new data for future ML training in a local SQL file.
    """
    settings.DB_DIR.mkdir(parents=True, exist_ok=True)
    sql_file = settings.SQL_EXPORT_PATH

    lines = [
        "-- RailPulse Collected Live Telemetry & Predictions Dump",
        f"-- Generated at: {datetime.now().isoformat()}",
        "-- Useful for future retraining and historical dataset augmentation\n",
        "BEGIN TRANSACTION;\n"
    ]

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Dump journey_telemetry_log
        cursor.execute("SELECT * FROM journey_telemetry_log")
        rows = cursor.fetchall()
        for r in rows:
            safe_payload = (r["raw_payload"] or "").replace("'", "''")
            lines.append(
                f"INSERT INTO journey_telemetry_log (train_no, journey_date, event_type, timestamp, station_code, current_speed_kmph, estimated_delay_so_far_min, actual_delay_min, raw_payload) "
                f"VALUES ('{r['train_no']}', '{r['journey_date']}', '{r['event_type']}', '{r['timestamp']}', '{r['station_code']}', {r['current_speed_kmph'] or 0}, {r['estimated_delay_so_far_min'] or 0}, {r['actual_delay_min'] or 'NULL'}, '{safe_payload}');"
            )

        # Dump predictions_log
        cursor.execute("SELECT * FROM predictions_log")
        p_rows = cursor.fetchall()
        for p in p_rows:
            lines.append(
                f"INSERT INTO predictions_log (train_no, station_seq, current_delay_min, to_station, p50_delay_min, p90_delay_min, method) "
                f"VALUES ('{p['train_no']}', {p['station_seq']}, {p['current_delay_min']}, '{p['to_station']}', {p['p50_delay_min']}, {p['p90_delay_min']}, '{p['method']}');"
            )

        lines.append("\nCOMMIT;\n")

    content = "\n".join(lines)
    sql_file.write_text(content, encoding="utf-8")
    return str(sql_file)
