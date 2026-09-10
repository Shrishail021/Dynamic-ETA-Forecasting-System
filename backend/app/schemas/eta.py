from typing import Optional
from pydantic import BaseModel, Field


class ETARequest(BaseModel):
    train_no: str
    current_station_seq: int = Field(
        ..., description="The last station the train has confirmed departure from (seq index).")
    current_delay_min: float = Field(
        0.0, description="Known delay (minutes) as of departure from current_station_seq.")
    as_of: Optional[str] = Field(
        None, description="ISO datetime this reading was taken. Defaults to now if omitted.")


class SectionETA(BaseModel):
    to_station: str
    predicted_arrival_delay_min: float
    p50_delay_min: float
    p90_delay_min: float
    method: str  # "naive_baseline" | "gbm_model"


class ETAResponse(BaseModel):
    train_no: str
    train_name: str
    generated_from_station_seq: int
    upcoming_stations: list[SectionETA]
    model_used: str
    disclaimer: str = (
        "Prediction generated on simulated/prototype data. Not real Indian "
        "Railways operational data."
    )
