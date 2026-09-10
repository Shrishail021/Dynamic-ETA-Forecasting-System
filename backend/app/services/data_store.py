"""
Persistent DataStore layer for RailPulse.
Queries SQLite backend (seeded from data/railway_eta_dataset/data/ on first run)
and keeps pandas DataFrames available for high-throughput ML inference.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from app.db.database import get_db_connection, init_db
from app.core.config import settings


class DataStore:
    def __init__(self):
        self._loaded = False
        self.stations = None
        self.sections = None
        self.trains = None
        self.schedule = None

    def load(self):
        # Initialize schema and seed CSVs if needed
        init_db()

        with get_db_connection() as conn:
            self.stations = pd.read_sql_query("SELECT * FROM stations", conn)
            self.sections = pd.read_sql_query("SELECT * FROM sections ORDER BY route_id, seq", conn)
            self.trains = pd.read_sql_query("SELECT * FROM trains", conn, dtype={"train_no": str})
            self.schedule = pd.read_sql_query("SELECT * FROM schedule ORDER BY train_no, seq", conn, dtype={"train_no": str})

        self._loaded = True
        return self

    def ensure_loaded(self):
        if not self._loaded or self.trains is None:
            self.load()
        return self

    def refresh(self):
        """Reload DataFrames from SQLite to keep in sync with updates."""
        return self.load()

    def train_row(self, train_no: str) -> Optional[Dict[str, Any]]:
        self.ensure_loaded()
        rows = self.trains[self.trains["train_no"] == str(train_no)]
        if rows.empty:
            return None
        return rows.iloc[0].to_dict()

    def schedule_for(self, train_no: str) -> List[Dict[str, Any]]:
        self.ensure_loaded()
        rows = self.schedule[self.schedule["train_no"] == str(train_no)].sort_values("seq")
        if rows.empty:
            return []

        # Merge with stations to include coordinates and full name for map rendering
        merged = rows.merge(
            self.stations[["station_code", "station_name", "latitude", "longitude"]],
            on="station_code",
            how="left"
        )
        return merged.to_dict(orient="records")

    def sections_for_route(self, route_id: str) -> List[Dict[str, Any]]:
        self.ensure_loaded()
        rows = self.sections[self.sections["route_id"] == str(route_id)].sort_values("seq")
        return rows.to_dict(orient="records")

    def find_nearest_station(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Calculates Haversine distance from given GPS coordinates to all stations.
        Returns nearest station and passing trains.
        """
        import math
        self.ensure_loaded()
        stations = self.stations.copy()

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371.0  # Earth radius in km
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c

        distances = []
        for _, s in stations.iterrows():
            if pd.notnull(s["latitude"]) and pd.notnull(s["longitude"]):
                d = haversine(lat, lon, float(s["latitude"]), float(s["longitude"]))
                distances.append((d, s.to_dict()))

        if not distances:
            return {}

        distances.sort(key=lambda x: x[0])
        nearest_km, nearest_station = distances[0]

        # Find trains that have this station in their schedule
        matching_train_nos = self.schedule[
            self.schedule["station_code"] == nearest_station["station_code"]
        ]["train_no"].unique()

        trains_df = self.trains[self.trains["train_no"].isin(matching_train_nos)]
        train_records = trains_df.to_dict(orient="records")
        for r in train_records:
            r["days_of_week"] = [int(x) for x in str(r["days_of_week"]).split("|") if x.strip()]

        return {
            "nearest_station": nearest_station,
            "distance_km": round(nearest_km, 1),
            "passing_trains": train_records,
            "total_trains": len(train_records),
        }

    def save_train(self, train_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves or updates a train in SQLite and refreshes memory."""
        train_no = str(train_data["train_no"])
        days_str = (
            "|".join(str(d) for d in train_data["days_of_week"])
            if isinstance(train_data.get("days_of_week"), list)
            else str(train_data.get("days_of_week", "0|1|2|3|4|5|6"))
        )

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO trains (
                    train_no, train_name, route_id, train_type,
                    priority, recovery_fraction, days_of_week, origin_departure_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                train_no,
                str(train_data["train_name"]),
                str(train_data["route_id"]),
                str(train_data["train_type"]),
                int(train_data["priority"]),
                float(train_data["recovery_fraction"]),
                days_str,
                str(train_data["origin_departure_time"]),
            ))
            conn.commit()

        self.refresh()
        return self.train_row(train_no)

    def delete_train(self, train_no: str) -> bool:
        """Deletes train and cascading schedule from SQLite."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM schedule WHERE train_no = ?", (str(train_no),))
            cursor.execute("DELETE FROM trains WHERE train_no = ?", (str(train_no),))
            conn.commit()
            affected = cursor.rowcount > 0

        self.refresh()
        return affected

    def generate_and_save_schedule(self, train_no: str, route_id: str,
                                   origin_dep_time: str = "10:00",
                                   recovery_fraction: float = 0.06) -> List[Dict[str, Any]]:
        """
        Auto-generates schedule stops from route sections if a new train doesn't have one.
        Solves Task 6 from MASTER_PROMPT_ANTIGRAVITY.md!
        """
        sections = self.sections_for_route(route_id)
        if not sections:
            return []

        # Determine origin and sequential stations
        schedule_rows = []
        origin_code = sections[0]["from_code"]
        current_km = 0.0
        current_time_min = 0.0  # minutes from origin

        # Stop 1: Origin
        schedule_rows.append({
            "train_no": str(train_no),
            "seq": 1,
            "station_code": origin_code,
            "distance_from_origin_km": 0.0,
            "scheduled_arrival_min": 0.0,
            "scheduled_departure_min": 0.0,
            "halt_min": 0.0
        })

        for sec in sections:
            dist = float(sec["distance_km"])
            avg_speed = float(sec["scheduled_avg_speed_kmph"]) or 75.0
            travel_min = (dist / avg_speed) * 60.0
            # add recovery buffer
            travel_min *= (1.0 + float(recovery_fraction))

            arrival_min = round(current_time_min + travel_min, 1)
            halt = float(sec["halt_min_at_to"])
            dep_min = round(arrival_min + halt, 1)

            current_km += dist
            current_time_min = dep_min

            schedule_rows.append({
                "train_no": str(train_no),
                "seq": int(sec["seq"]) + 1,
                "station_code": sec["to_code"],
                "distance_from_origin_km": round(current_km, 1),
                "scheduled_arrival_min": arrival_min,
                "scheduled_departure_min": dep_min,
                "halt_min": halt
            })

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM schedule WHERE train_no = ?", (str(train_no),))
            for s in schedule_rows:
                cursor.execute("""
                    INSERT INTO schedule (train_no, seq, station_code, distance_from_origin_km,
                                          scheduled_arrival_min, scheduled_departure_min, halt_min)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    s["train_no"], s["seq"], s["station_code"],
                    s["distance_from_origin_km"], s["scheduled_arrival_min"],
                    s["scheduled_departure_min"], s["halt_min"]
                ))
            conn.commit()

        self.refresh()
        return self.schedule_for(train_no)


# Module-level singleton
data_store = DataStore()
