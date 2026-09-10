import asyncio
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.live_feed_service import stream_journey_events
from app.services.eta_service import model_based_eta
from app.services.telemetry_service import log_journey_event, log_prediction

router = APIRouter()


@router.get("/{train_no}/stream")
async def live_stream(train_no: str, date: str, seed: int | None = None, speed: float = 200.0):
    """
    Server-Sent-Events stream of a live simulated train journey.
    On every 'position' ping, runs dynamic re-forecasting (Task 4)
    using the train's current estimated delay, and attaches the updated
    per-station ETA confidence bands (p50/p90) into the SSE payload.
    Also logs the telemetry and predictions to SQLite for future training.
    """
    try:
        events = stream_journey_events(train_no, date, seed=seed)
    except Exception as e:
        raise HTTPException(400, f"Could not start simulation: {e}")

    async def event_generator():
        prev_ts = None
        current_seq = 1

        for ev in events:
            event_type = ev.get("event")

            # Update station sequence tracker
            if event_type == "departure":
                current_seq = int(ev.get("from_seq", current_seq))
            elif event_type == "arrival":
                current_seq = int(ev.get("station_seq", current_seq))
            elif event_type == "position":
                current_seq = int(ev.get("from_seq", current_seq))

            # Dynamic re-forecasting on each position event (or departure)
            delay_so_far = float(ev.get("estimated_delay_so_far_min", 0.0))
            if event_type in ("position", "departure"):
                try:
                    reforecast = model_based_eta(train_no, current_seq, delay_so_far, as_of=ev.get("timestamp"))
                    ev["dynamic_eta"] = reforecast
                    if reforecast:
                        ev["next_station_eta"] = reforecast[0]

                        # Log prediction to SQLite for future evaluation & training
                        for p in reforecast:
                            log_prediction(
                                train_no=train_no,
                                station_seq=current_seq,
                                current_delay_min=delay_so_far,
                                to_station=p["to_station"],
                                p50_delay_min=p["p50_delay_min"],
                                p90_delay_min=p["p90_delay_min"],
                                method=p["method"],
                            )
                except Exception as exc:
                    ev["reforecast_error"] = str(exc)

            # Log journey telemetry to SQLite
            try:
                log_journey_event(train_no, date, ev)
            except Exception:
                pass

            # Yield SSE data packet
            yield f"data: {json.dumps(ev)}\n\n"

            # Dynamic throttle according to simulation speed multiplier
            ts_str = ev.get("timestamp") or ev.get("actual_time")
            if ts_str and prev_ts:
                try:
                    ts = datetime.fromisoformat(ts_str)
                    gap = (ts - prev_ts).total_seconds() / max(speed, 1.0)
                    await asyncio.sleep(min(max(gap, 0), 2.0))
                except Exception:
                    await asyncio.sleep(0.05)

            if ts_str:
                try:
                    prev_ts = datetime.fromisoformat(ts_str)
                except Exception:
                    pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")


from pydantic import BaseModel
from typing import Optional


class RailRadarIngestPayload(BaseModel):
    train_no: str
    current_lat: Optional[float] = None
    current_lon: Optional[float] = None
    current_speed_kmph: Optional[float] = 95.0
    last_station_code: Optional[str] = None
    last_station_seq: Optional[int] = None
    observed_delay_min: float = 0.0
    timestamp: Optional[str] = None


@router.post("/railradar-adapter")
def ingest_live_railradar_feed(payload: RailRadarIngestPayload):
    """
    Live API Ingestion Adapter for RailRadar / NTES / GPS Locomotive Trackers.
    Accepts real-time position updates, infers TSR/speed anomalies,
    and dynamically predicts downstream delays using autoregressive quantile ML.
    """
    from app.services.data_store import data_store

    data_store.ensure_loaded()
    train_row = data_store.train_row(payload.train_no)
    if not train_row:
        raise HTTPException(404, f"Train {payload.train_no} not recognized in train master.")

    schedule = data_store.schedule_for(payload.train_no)
    sections = data_store.sections_for_route(train_row["route_id"])

    # Determine station sequence
    seq = payload.last_station_seq
    if not seq and payload.last_station_code:
        matching_stop = next((s for s in schedule if s["station_code"] == payload.last_station_code), None)
        if matching_stop:
            seq = matching_stop["seq"]
    if not seq and payload.current_lat and payload.current_lon:
        # Find nearest station from GPS
        nearest_lookup = data_store.find_nearest_station(payload.current_lat, payload.current_lon)
        if nearest_lookup:
            nearest_code = nearest_lookup["nearest_station"]["station_code"]
            matching_stop = next((s for s in schedule if s["station_code"] == nearest_code), None)
            if matching_stop:
                seq = matching_stop["seq"]

    seq = seq or 1

    # Detect speed anomaly (proxy for Temporary Speed Restriction without official feed)
    active_section = next((s for s in sections if s["seq"] == seq), {})
    permissible_speed = float(active_section.get("permissible_speed_kmph", 130.0))
    speed_anomaly = (
        payload.current_speed_kmph is not None
        and payload.current_speed_kmph > 0
        and payload.current_speed_kmph < (permissible_speed * 0.65)
    )

    # Dynamic ML forecast
    reforecast = model_based_eta(
        train_no=payload.train_no,
        current_station_seq=seq,
        current_delay_min=payload.observed_delay_min,
        as_of=payload.timestamp or datetime.now().isoformat()
    )

    # Log to telemetry database for future prediction retraining
    log_journey_event(
        train_no=payload.train_no,
        journey_date=datetime.now().strftime("%Y-%m-%d"),
        event_data={
            "event": "railradar_ping",
            "timestamp": payload.timestamp or datetime.now().isoformat(),
            "station": payload.last_station_code or (schedule[seq - 1]["station_code"] if schedule else ""),
            "speed_kmph": payload.current_speed_kmph,
            "estimated_delay_so_far_min": payload.observed_delay_min,
            "speed_anomaly": speed_anomaly,
            "source": "RailRadar_API_Adapter"
        }
    )

    return {
        "status": "processed",
        "train_no": payload.train_no,
        "train_name": train_row["train_name"],
        "route_id": train_row["route_id"],
        "checkpoint_seq": seq,
        "observed_delay_min": payload.observed_delay_min,
        "current_speed_kmph": payload.current_speed_kmph,
        "sectional_permissible_speed_kmph": permissible_speed,
        "speed_anomaly_detected": speed_anomaly,
        "inferred_advisories": {
            "is_fog_prone": bool(active_section.get("fog_prone", False)),
            "congestion_level": float(active_section.get("congestion_level", 0.3)),
            "inferred_temporary_speed_restriction": speed_anomaly,
        },
        "dynamic_eta_forecast": reforecast,
        "problem_addressed": {
            "description": "Replaces static timetable extrapolation (which fails during fog, TSRs, and compounding cascades) with dynamic section-level ML forecasting.",
            "uncertainty_intervals": "Provides P50 likely arrival and P90 confidence upper-bound to give dispatchers realistic safety cushions."
        }
    }

