from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.data_store import data_store
from app.schemas.train import Train, TrainWithSchedule

router = APIRouter()


@router.get("", response_model=list[Train])
def list_trains(
    route_id: Optional[str] = None,
    train_type: Optional[str] = None,
    search: Optional[str] = Query(None, description="Search train number, name, or station code")
):
    """
    Browse/search trains. Public — no auth required.
    Supports filtering by route_id, train_type, and text search (train_no or train_name).
    """
    data_store.ensure_loaded()
    df = data_store.trains

    if route_id:
        df = df[df["route_id"] == route_id]
    if train_type:
        df = df[df["train_type"] == train_type]
    if search:
        s = str(search).strip().lower()
        sched = data_store.schedule
        matching_st_trains = []
        if sched is not None and not sched.empty:
            st_matches = sched[sched["station_code"].str.lower().str.contains(s, na=False)]["train_no"].unique().tolist()
            matching_st_trains = [str(x) for x in st_matches]

        df = df[
            df["train_no"].str.lower().str.contains(s, na=False) |
            df["train_name"].str.lower().str.contains(s, na=False) |
            df["train_no"].isin(matching_st_trains)
        ]

    records = df.to_dict(orient="records")

    for r in records:
        r["days_of_week"] = [int(x) for x in str(r["days_of_week"]).split("|") if x.strip()]
    return records


@router.get("/nearby")
def get_nearby_trains(lat: float = Query(..., description="Latitude"), lon: float = Query(..., description="Longitude")):
    """
    GPS Geolocation station and train lookup.
    Takes user's latitude and longitude, finds nearest Indian Railway station,
    and returns all passing and departing trains.
    """
    data_store.ensure_loaded()
    result = data_store.find_nearest_station(lat, lon)
    if not result:
        raise HTTPException(404, "No stations with valid coordinates found in network")
    return result


@router.get("/{train_no}", response_model=TrainWithSchedule)
def get_train(train_no: str):
    """Train detail + full schedule. Public."""
    row = data_store.train_row(train_no)
    if row is None:
        raise HTTPException(404, f"Train {train_no} not found")
    row["days_of_week"] = [int(x) for x in str(row["days_of_week"]).split("|") if x.strip()]
    row["schedule"] = data_store.schedule_for(train_no)
    return row

