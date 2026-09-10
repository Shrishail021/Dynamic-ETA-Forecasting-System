"""Builds each train's full station-by-station schedule (distance-from-origin
and scheduled time offsets in minutes from the train's origin departure)."""

from .network import sections_for_route, ROUTE_ORIGIN, STATIONS

# Fixed illustrative origin-departure clock time per train_no ("HH:MM").
# In reality this comes from the working timetable; here it's just enough
# to give each train a believable, fixed daily slot (which matters for the
# fog/peak-hour logic in dynamics.py).
ORIGIN_DEPARTURE_TIME = {
    "12951": "16:00", "19269": "23:00", "12459": "07:20", "14673": "21:10",
    "12007": "06:00", "16021": "21:45", "12302": "16:55", "13005": "19:15",
    "56215": "06:30", "06231": "17:45",
}


def build_train_schedule(train):
    """Return list of stops: dicts with station_code, seq, distance_from_origin_km,
    scheduled_arrival_min (offset from origin departure), scheduled_departure_min,
    halt_min. seq=0 is the origin (no arrival)."""
    secs = sections_for_route(train.route_id)
    origin = ROUTE_ORIGIN[train.route_id]
    stops = [{
        "station_code": origin, "seq": 0,
        "distance_from_origin_km": 0.0,
        "scheduled_arrival_min": 0, "scheduled_departure_min": 0,
        "halt_min": 0,
    }]
    cum_dist = 0.0
    cum_time = 0
    for sec in secs:
        cum_dist += sec.distance_km
        cum_time += sec.scheduled_min
        arr = cum_time
        dep = cum_time + sec.halt_min_at_to
        stops.append({
            "station_code": sec.to_code, "seq": sec.seq,
            "distance_from_origin_km": cum_dist,
            "scheduled_arrival_min": arr, "scheduled_departure_min": dep,
            "halt_min": sec.halt_min_at_to,
        })
        cum_time = dep
    return stops
