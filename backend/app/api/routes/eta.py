from fastapi import APIRouter, HTTPException
from app.schemas.eta import ETARequest, ETAResponse, SectionETA
from app.services.data_store import data_store
from app.services.eta_service import naive_baseline_eta, model_based_eta

router = APIRouter()


@router.post("/predict", response_model=ETAResponse)
def predict_eta(req: ETARequest, use_model: bool = True):
    """Predict ETA at all upcoming stations for a train, given its last
    known station and delay. Public — this is what the passenger-facing
    live ETA page calls.

    `use_model=false` forces the naive baseline (useful for building the
    "our model vs today's method" comparison view in the admin dashboard).
    """
    train_row = data_store.train_row(req.train_no)
    if train_row is None:
        raise HTTPException(404, f"Train {req.train_no} not found")

    fn = model_based_eta if use_model else naive_baseline_eta
    results = fn(req.train_no, req.current_station_seq, req.current_delay_min)

    return ETAResponse(
        train_no=req.train_no,
        train_name=train_row["train_name"],
        generated_from_station_seq=req.current_station_seq,
        upcoming_stations=[SectionETA(**r) for r in results],
        model_used=results[0]["method"] if results else "n/a",
    )
