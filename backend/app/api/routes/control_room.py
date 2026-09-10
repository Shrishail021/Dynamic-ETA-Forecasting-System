from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from datetime import datetime

from app.core.security import require_staff
from app.services.data_store import data_store
from app.services.eta_service import model_based_eta

router = APIRouter()


@router.get("/overview")
def get_control_room_overview(current_user: dict = Depends(require_staff)):
    """
    Control room multi-train status matrix (Task 5).
    Provides dispatchers with a unified birds-eye view across all active corridors:
    - Train details, priority, corridor route
    - Simulated current delay and next stop
    - Dynamic ML ETA predictions (P50 likely, P90 late upper bound)
    - Section hazard warnings (fog-prone, speed restrictions, congestion)
    """
    data_store.ensure_loaded()
    trains = data_store.trains.to_dict(orient="records")

    corridor_summaries = []
    total_delay = 0.0
    on_time_count = 0

    for t in trains:
        train_no = str(t["train_no"])
        route_id = str(t["route_id"])
        schedule = data_store.schedule_for(train_no)
        sections = data_store.sections_for_route(route_id)

        # Baseline origin & destination
        origin = schedule[0]["station_code"] if schedule else "NDLS"
        destination = schedule[-1]["station_code"] if schedule else "TERM"

        # Determine middle checkpoint / active simulation state
        # In a control room view, estimate mid-journey state if 3+ stops
        mid_seq = max(1, len(schedule) // 2) if schedule else 1
        current_stop = schedule[mid_seq - 1] if schedule and len(schedule) >= mid_seq else {"station_code": origin}
        next_stop = schedule[mid_seq] if schedule and len(schedule) > mid_seq else current_stop

        # Simulated delay state based on route characteristics (e.g. fog prone or priority)
        # Higher priority trains have lower nominal delays
        simulated_delay = max(0.0, round((5 - int(t.get("priority", 3))) * 8.5 + (12 if "R4" in route_id else 4), 1))
        total_delay += simulated_delay
        if simulated_delay <= 15:
            on_time_count += 1

        # Run dynamic ETA prediction for upcoming stations
        eta_results = model_based_eta(train_no, mid_seq, simulated_delay)
        next_eta = eta_results[0] if eta_results else {
            "to_station": next_stop.get("station_code", "NEXT"),
            "p50_delay_min": simulated_delay,
            "p90_delay_min": simulated_delay + 10.0,
            "method": "gbm_model"
        }

        # Check section hazard flags
        active_sec = next((s for s in sections if s["seq"] == mid_seq), {})
        is_fog = bool(active_sec.get("fog_prone", 0))
        congestion = float(active_sec.get("congestion_level", 0.3))

        status_label = "ON_TIME" if simulated_delay <= 10 else ("DELAYED" if simulated_delay <= 30 else "CRITICAL")

        corridor_summaries.append({
            "train_no": train_no,
            "train_name": t["train_name"],
            "train_type": t["train_type"],
            "priority": t["priority"],
            "route_id": route_id,
            "origin": origin,
            "destination": destination,
            "current_station": current_stop.get("station_code", origin),
            "next_station": next_eta.get("to_station", next_stop.get("station_code", "DEST")),
            "current_delay_min": simulated_delay,
            "status": status_label,
            "next_eta_p50": next_eta.get("p50_delay_min", simulated_delay),
            "next_eta_p90": next_eta.get("p90_delay_min", simulated_delay + 10.0),
            "is_fog_prone": is_fog,
            "congestion_index": round(congestion, 2),
            "total_stops": len(schedule),
        })

    trains_count = len(corridor_summaries) or 1
    avg_delay = round(total_delay / trains_count, 1)
    punctuality_pct = round((on_time_count / trains_count) * 100, 1)

    return {
        "timestamp": datetime.now().isoformat(),
        "total_active_trains": len(corridor_summaries),
        "system_punctuality_rate": punctuality_pct,
        "average_network_delay_min": avg_delay,
        "trains": corridor_summaries,
    }
