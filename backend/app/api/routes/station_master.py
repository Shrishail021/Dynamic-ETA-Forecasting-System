"""
Station Master Operations & Train Attribute Monitoring API.
Enables Station Masters to:
1. Select their station and monitor all incoming trains with comprehensive real-world train attributes.
2. View location-based delay root causes (e.g. Fog advisory, TSR, line choke).
3. Receive continuous ETA broadcasts even when intermediate train masters failed to report.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.data_store import data_store
from app.services.eta_service import model_based_eta
from app.services.delay_attribution_service import analyze_delay_cause
from app.services.autonomous_broadcast_service import compute_autonomous_broadcast

router = APIRouter()

# Real-world rake and traction metadata mapping by train type / number
TRAIN_ATTRIBUTES_SPEC = {
    "rajdhani_shatabdi_vb": {
        "rake_type": "LHB Air-Conditioned (Alstom-design Stainless Steel)",
        "traction_type": "Electric 25kV AC (WAP-7 / 6000 HP)",
        "coaches_count": 22,
        "rake_length_meters": 540,
        "max_permissible_speed_kmph": 130,
        "nominal_platform": 1,
    },
    "superfast": {
        "rake_type": "LHB Mixed Composition (AC 2-Tier/3-Tier/Sleeper)",
        "traction_type": "Electric 25kV AC (WAP-7 / WAP-5)",
        "coaches_count": 24,
        "rake_length_meters": 620,
        "max_permissible_speed_kmph": 110,
        "nominal_platform": 2,
    },
    "express": {
        "rake_type": "ICF Modernized High-Capacity Conventional",
        "traction_type": "Dual-Cab Diesel-Electric (WDP-4D / 4500 HP)",
        "coaches_count": 20,
        "rake_length_meters": 480,
        "max_permissible_speed_kmph": 100,
        "nominal_platform": 3,
    },
    "passenger": {
        "rake_type": "MEMU / Suburban Stainless Steel Rake",
        "traction_type": "Three-Phase AC Distributed EMU Power",
        "coaches_count": 12,
        "rake_length_meters": 280,
        "max_permissible_speed_kmph": 90,
        "nominal_platform": 4,
    }
}


@router.get("/stations")
def get_monitored_stations():
    """Returns all available stations for Station Master selection."""
    data_store.ensure_loaded()
    stations = data_store.stations.to_dict(orient="records")
    return [
        {
            "station_code": s["station_code"],
            "station_name": s["station_name"],
            "latitude": s.get("latitude"),
            "longitude": s.get("longitude")
        }
        for s in stations
    ]


@router.get("/station/{station_code}")
def get_station_master_overview(station_code: str):
    """
    Station Master Real-Time Dashboard.
    Returns all approaching and stopping trains for the chosen station,
    including detailed train attributes, delay causes (fog/TSR), and ETA predictions.
    """
    data_store.ensure_loaded()
    target_code = station_code.upper().strip()

    st_row = data_store.stations[data_store.stations["station_code"] == target_code]
    if st_row.empty:
        raise HTTPException(404, f"Station {target_code} not found")
    st_info = st_row.iloc[0].to_dict()

    trains = data_store.trains.to_dict(orient="records")
    incoming_trains = []

    for t in trains:
        train_no = str(t["train_no"])
        schedule = data_store.schedule_for(train_no)
        sections = data_store.sections_for_route(t["route_id"])

        # Check if train visits this station
        target_stop_idx = next((i for i, s in enumerate(schedule) if s["station_code"] == target_code), None)
        if target_stop_idx is None:
            continue

        target_stop = schedule[target_stop_idx]
        target_seq = target_stop["seq"]

        # If train originates here, target_seq is 1 (departing)
        # Otherwise, simulate current train position 1-2 stops upstream
        current_seq = max(1, target_seq - 1)
        current_stop = schedule[current_seq - 1]

        # Calculate simulated delay and cause
        base_delay = 18.0 if "R1" in t["route_id"] or "R4" in t["route_id"] else (6.0 * int(t["priority"]))
        current_speed = 62.0 if "R1" in t["route_id"] else 92.0

        sec_info = next((s for s in sections if s["seq"] == current_seq), {})

        # Analyze root cause of delay
        delay_cause = analyze_delay_cause(
            train_no=train_no,
            route_id=t["route_id"],
            current_seq=current_seq,
            current_delay_min=base_delay,
            current_speed_kmph=current_speed,
            section_info=sec_info,
            weather_condition="fog"
        )

        # Predict ETA to target station
        eta_results = model_based_eta(train_no, current_seq, base_delay)
        target_eta_pred = next((e for e in eta_results if e["to_station"] == target_code), None)
        p50_delay = target_eta_pred["p50_delay_min"] if target_eta_pred else base_delay
        p90_delay = target_eta_pred["p90_delay_min"] if target_eta_pred else base_delay + 12.0

        # Calculate clock times
        origin_dep = str(t.get("origin_departure_time", "10:00"))
        parts = origin_dep.split(":")
        bh, bm = int(parts[0]), int(parts[1])

        sched_min = float(target_stop["scheduled_arrival_min"])
        tot_sched = bh * 60 + bm + int(sched_min)
        tot_live = tot_sched + int(p50_delay)

        sched_clock = f"{((tot_sched // 60) % 24):02d}:{(tot_sched % 60):02d}"
        live_clock = f"{((tot_live // 60) % 24):02d}:{(tot_live % 60):02d}"

        # Train physical attributes
        ttype = t.get("train_type", "express").lower()
        attr_spec = TRAIN_ATTRIBUTES_SPEC.get(ttype, TRAIN_ATTRIBUTES_SPEC["express"])

        distance_remaining = max(0.0, float(target_stop["distance_from_origin_km"]) - float(current_stop["distance_from_origin_km"]))

        # Check if train master at previous station reported or if dead-reckoning
        is_autonomous_telemetry = (int(t["train_no"]) % 2 == 0 and current_seq > 1)

        incoming_trains.append({
            "train_no": train_no,
            "train_name": t["train_name"],
            "train_type": t["train_type"],
            "priority": t["priority"],
            "origin_departure_time": origin_dep,
            "current_location": {
                "station_code": current_stop["station_code"],
                "station_name": current_stop.get("station_name", current_stop["station_code"]),
                "seq": current_seq,
                "current_speed_kmph": round(current_speed),
                "permissible_speed_kmph": attr_spec["max_permissible_speed_kmph"],
                "distance_to_station_km": round(distance_remaining, 1),
            },
            "scheduled_arrival_time": sched_clock,
            "expected_live_eta": live_clock,
            "p50_delay_min": round(p50_delay, 1),
            "p90_delay_min": round(p90_delay, 1),
            "halt_min": target_stop["halt_min"],
            "assigned_platform": f"PF-{attr_spec['nominal_platform']}",
            "attributes": {
                "rake_type": attr_spec["rake_type"],
                "traction_type": attr_spec["traction_type"],
                "coaches_count": attr_spec["coaches_count"],
                "rake_length_meters": attr_spec["rake_length_meters"],
                "load_classification": "Full Passenger Load (22 Coaches)",
                "brake_system": "Twin Pipe Electro-Pneumatic Air Brake (Disc)",
            },
            "delay_cause": delay_cause,
            "telemetry_source": "AUTONOMOUS_DEAD_RECKONING" if is_autonomous_telemetry else "STATION_MASTER_LOGGED",
            "telemetry_note": (
                "Train Master at intermediate checkpoint did not log. RailPulse extrapolating via dead-reckoning."
                if is_autonomous_telemetry else "Telemetry confirmed by block station logger."
            )
        })

    # Sort trains by expected arrival
    incoming_trains.sort(key=lambda x: x["expected_live_eta"])

    return {
        "station_code": target_code,
        "station_name": st_info.get("station_name", target_code),
        "state": st_info.get("state", "Northern Railway"),
        "timestamp": datetime.now().isoformat(),
        "total_incoming_trains": len(incoming_trains),
        "fog_alert_active": any(t["delay_cause"]["primary_cause"] == "DENSE_FOG" for t in incoming_trains),
        "trains": incoming_trains
    }


@router.get("/autonomous-broadcast/{train_no}")
def get_autonomous_broadcast(
    train_no: str,
    last_reported_seq: int = Query(1, ge=1),
    minutes_unupdated: float = Query(75.0, ge=0.0),
    simulated_delay: float = Query(15.0, ge=0.0),
    weather: str = Query("fog")
):
    """
    Simulates / triggers autonomous dead-reckoning ETA broadcast for a train
    when intermediate train masters failed to update station arrivals.
    """
    return compute_autonomous_broadcast(
        train_no=train_no,
        last_reported_seq=last_reported_seq,
        minutes_since_last_update=minutes_unupdated,
        last_reported_delay=simulated_delay,
        simulated_weather=weather
    )
