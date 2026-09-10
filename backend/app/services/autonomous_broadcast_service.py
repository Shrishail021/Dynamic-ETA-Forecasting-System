"""
Autonomous Dead-Reckoning ETA Broadcast Engine.
Broadcasts dynamic ETAs and continuously predicts downstream delays even when
the train master / station logger has not manually logged train arrival/departure.
Uses elapsed transit time, track geometry, section permissible speeds, and
weather constraints (fog speed cap) to extrapolate train progression.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.services.data_store import data_store
from app.services.eta_service import model_based_eta
from app.services.delay_attribution_service import analyze_delay_cause


def compute_autonomous_broadcast(
    train_no: str,
    last_reported_seq: int = 1,
    minutes_since_last_update: float = 60.0,
    last_reported_delay: float = 10.0,
    simulated_weather: str = "fog"
) -> Dict[str, Any]:
    """
    Computes real-time train progression and downstream ETA broadcast
    when the Train Master has not logged recent station updates.
    """
    data_store.ensure_loaded()
    train = data_store.train_row(train_no)
    if not train:
        return {"error": f"Train {train_no} not found"}

    schedule = data_store.schedule_for(train_no)
    sections = data_store.sections_for_route(train["route_id"])

    if not schedule:
        return {"error": f"No schedule found for train {train_no}"}

    # Find the last station checkpoint logged by the train master
    last_stop_idx = min(max(0, last_reported_seq - 1), len(schedule) - 1)
    last_logged_stop = schedule[last_stop_idx]

    # Baseline minutes from origin when the train master last logged
    last_logged_origin_min = float(last_logged_stop.get("scheduled_departure_min", 0.0))
    current_elapsed_journey_min = last_logged_origin_min + float(last_reported_delay) + float(minutes_since_last_update)

    # Dead reckoning progression loop: extrapolate which section the train is physically traversing
    current_estimated_seq = last_reported_seq
    estimated_distance_km = float(last_logged_stop.get("distance_from_origin_km", 0.0))
    estimated_speed = 85.0
    active_section = {}
    accumulated_delay = float(last_reported_delay)
    master_missed_stations = []

    # Check downstream stops
    for stop in schedule:
        if stop["seq"] <= last_reported_seq:
            continue

        sched_arr_min = float(stop["scheduled_arrival_min"])
        sched_dep_min = float(stop["scheduled_departure_min"])
        sec = next((s for s in sections if s["seq"] == stop["seq"] - 1), {})
        is_fog = bool(sec.get("fog_prone", 0)) or simulated_weather == "fog"
        permissible_spd = float(sec.get("permissible_speed_kmph", 130.0))
        speed_cap = 60.0 if is_fog else permissible_spd

        # If elapsed time is greater than scheduled arrival + delay, train has passed or reached this stop
        if current_elapsed_journey_min >= (sched_arr_min + accumulated_delay):
            current_estimated_seq = stop["seq"]
            estimated_distance_km = float(stop["distance_from_origin_km"])
            master_missed_stations.append({
                "station_code": stop["station_code"],
                "station_name": stop.get("station_name", stop["station_code"]),
                "scheduled_arrival_min": sched_arr_min,
                "status": "UNREPORTED_BY_STATION_MASTER"
            })
            # Add small propagation delay if running through fog/congestion
            if is_fog:
                accumulated_delay += 8.0
        else:
            # Train is currently in transit between previous stop and this stop
            prev_stop = schedule[stop["seq"] - 2] if stop["seq"] >= 2 else last_logged_stop
            sec_dist = float(stop["distance_from_origin_km"]) - float(prev_stop["distance_from_origin_km"])
            transit_fraction = max(0.1, min(0.9, (current_elapsed_journey_min - (float(prev_stop["scheduled_departure_min"]) + accumulated_delay)) / max(sec_dist / (speed_cap / 60.0), 1.0)))
            estimated_distance_km = float(prev_stop["distance_from_origin_km"]) + (sec_dist * transit_fraction)
            estimated_speed = speed_cap
            active_section = sec
            break

    # Cap at final terminus
    current_estimated_seq = min(current_estimated_seq, len(schedule))
    current_stop_obj = schedule[current_estimated_seq - 1]

    # Find next upcoming stop
    next_stop_obj = schedule[current_estimated_seq] if current_estimated_seq < len(schedule) else current_stop_obj

    if not active_section:
        active_section = next((s for s in sections if s["seq"] == current_estimated_seq), {})

    # Compute location-aware delay root cause
    delay_cause = analyze_delay_cause(
        train_no=train_no,
        route_id=train["route_id"],
        current_seq=current_estimated_seq,
        current_delay_min=accumulated_delay,
        current_speed_kmph=estimated_speed,
        section_info=active_section,
        weather_condition=simulated_weather
    )

    # Compute live downstream ML ETA forecast using the autoregressive quantile model
    ml_forecast = model_based_eta(train_no, current_estimated_seq, accumulated_delay)

    # Origin clock reference
    origin_dep = str(train.get("origin_departure_time", "10:00"))
    parts = origin_dep.split(":")
    base_h, base_m = int(parts[0]), int(parts[1])

    formatted_forecast = []
    for f in ml_forecast:
        st_obj = next((s for s in schedule if s["station_code"] == f["to_station"]), {})
        sched_min = float(st_obj.get("scheduled_arrival_min", 0.0))
        p50 = float(f.get("p50_delay_min", accumulated_delay))
        p90 = float(f.get("p90_delay_min", p50 + 12.0))

        tot_p50 = base_h * 60 + base_m + int(sched_min) + int(p50)
        tot_sched = base_h * 60 + base_m + int(sched_min)

        arr_p50_clock = f"{((tot_p50 // 60) % 24):02d}:{(tot_p50 % 60):02d}"
        arr_sched_clock = f"{((tot_sched // 60) % 24):02d}:{(tot_sched % 60):02d}"

        formatted_forecast.append({
            "to_station": f["to_station"],
            "station_name": st_obj.get("station_name", f["to_station"]),
            "scheduled_arrival_time": arr_sched_clock,
            "expected_live_eta": arr_p50_clock,
            "p50_delay_min": round(p50, 1),
            "p90_delay_min": round(p90, 1),
            "distance_from_origin_km": st_obj.get("distance_from_origin_km", 0.0),
            "halt_min": st_obj.get("halt_min", 2.0),
            "method": f.get("method", "gbm_model"),
        })

    is_unupdated = len(master_missed_stations) > 0 or minutes_since_last_update >= 30.0

    return {
        "train_no": train_no,
        "train_name": train["train_name"],
        "train_type": train["train_type"],
        "route_id": train["route_id"],
        "origin_departure_time": origin_dep,
        "broadcast_timestamp": datetime.now().isoformat(),
        "broadcast_mode": "AUTONOMOUS_DEAD_RECKONING" if is_unupdated else "STATION_MASTER_CONFIRMED",
        "telemetry_health": {
            "is_unupdated_by_train_master": is_unupdated,
            "minutes_since_last_update": minutes_since_last_update,
            "last_logged_station": last_logged_stop.get("station_code"),
            "last_logged_seq": last_reported_seq,
            "unreported_stations_count": len(master_missed_stations),
            "unreported_stations": master_missed_stations,
            "status_banner": (
                f"Train Master at {master_missed_stations[-1]['station_code'] if master_missed_stations else last_logged_stop['station_code']} "
                f"did not log update ({int(minutes_since_last_update)} min telemetry silence). "
                f"RailPulse is autonomously broadcasting dead-reckoning ETAs."
                if is_unupdated else "Train telemetry updated normally."
            )
        },
        "extrapolated_position": {
            "estimated_seq": current_estimated_seq,
            "current_station_code": current_stop_obj.get("station_code"),
            "current_station_name": current_stop_obj.get("station_name"),
            "approaching_station_code": next_stop_obj.get("station_code"),
            "approaching_station_name": next_stop_obj.get("station_name"),
            "estimated_distance_km": round(estimated_distance_km, 1),
            "current_speed_kmph": round(estimated_speed),
            "extrapolated_delay_min": round(accumulated_delay, 1),
        },
        "delay_cause_analysis": delay_cause,
        "dynamic_eta_broadcast": formatted_forecast,
    }
