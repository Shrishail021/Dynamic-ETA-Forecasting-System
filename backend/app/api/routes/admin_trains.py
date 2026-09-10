from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import require_admin
from app.services.data_store import data_store
from app.schemas.train import Train, TrainCreate

router = APIRouter()


@router.get("", response_model=list[Train], dependencies=[Depends(require_admin)])
def list_trains_admin():
    """Admin-facing list of all registered trains."""
    data_store.ensure_loaded()
    records = data_store.trains.to_dict(orient="records")
    for r in records:
        r["days_of_week"] = [int(x) for x in str(r["days_of_week"]).split("|") if x.strip()]
    return records


@router.post("", response_model=Train, dependencies=[Depends(require_admin)])
def create_train(payload: TrainCreate):
    """
    Creates a new train in SQLite.
    Validates train_no uniqueness and route existence.
    Auto-generates stop schedule along the chosen route so newly created
    trains immediately have valid schedule rows for simulation and ETA prediction.
    """
    data_store.ensure_loaded()

    # Validate train_no uniqueness
    if (data_store.trains["train_no"] == payload.train_no).any():
        raise HTTPException(status_code=409, detail=f"train_no {payload.train_no} already exists")

    # Validate route_id
    sections = data_store.sections_for_route(payload.route_id)
    if not sections:
        raise HTTPException(
            status_code=400,
            detail=f"route_id {payload.route_id} does not exist in network sections."
        )

    # Persist train record to SQLite
    train_dict = payload.dict()
    saved = data_store.save_train(train_dict)

    # Auto-generate schedule for this train based on route sections
    data_store.generate_and_save_schedule(
        train_no=payload.train_no,
        route_id=payload.route_id,
        origin_dep_time=payload.origin_departure_time,
        recovery_fraction=payload.recovery_fraction
    )

    return payload


@router.put("/{train_no}", response_model=Train, dependencies=[Depends(require_admin)])
def update_train(train_no: str, payload: TrainCreate):
    """Updates an existing train in SQLite."""
    data_store.ensure_loaded()
    existing = data_store.train_row(train_no)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Train {train_no} not found")

    train_dict = payload.dict()
    train_dict["train_no"] = train_no
    data_store.save_train(train_dict)

    # If route changed, regenerate schedule
    if existing.get("route_id") != payload.route_id:
        data_store.generate_and_save_schedule(
            train_no=train_no,
            route_id=payload.route_id,
            origin_dep_time=payload.origin_departure_time,
            recovery_fraction=payload.recovery_fraction
        )

    return payload


@router.delete("/{train_no}", dependencies=[Depends(require_admin)])
def delete_train(train_no: str):
    """Deletes train and cascading schedule records from SQLite."""
    data_store.ensure_loaded()
    success = data_store.delete_train(train_no)
    if not success:
        raise HTTPException(status_code=404, detail=f"Train {train_no} not found")
    return {"deleted": train_no, "message": "Train and schedule records removed."}
