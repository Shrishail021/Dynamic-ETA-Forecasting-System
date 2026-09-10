from typing import Optional, List
from pydantic import BaseModel


class Station(BaseModel):
    station_code: str
    station_name: str
    latitude: float
    longitude: float


class Section(BaseModel):
    route_id: str
    seq: int
    from_code: str
    to_code: str
    distance_km: float
    scheduled_min: int
    scheduled_avg_speed_kmph: float
    permissible_speed_kmph: int
    terrain: str
    fog_prone: bool
    congestion_level: float
    halt_min_at_to: int


class Train(BaseModel):
    train_no: str
    train_name: str
    route_id: str
    train_type: str
    priority: int
    recovery_fraction: float
    days_of_week: List[int]
    origin_departure_time: str


class TrainCreate(BaseModel):
    """Payload for admin-created/edited trains.
    TODO(Antigravity): once sections/routes are also admin-editable,
    validate route_id against the sections table before accepting this."""
    train_no: str
    train_name: str
    route_id: str
    train_type: str
    priority: int
    recovery_fraction: float
    days_of_week: List[int]
    origin_departure_time: str


class ScheduleStop(BaseModel):
    train_no: str
    seq: int
    station_code: str
    station_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_from_origin_km: float
    scheduled_arrival_min: float
    scheduled_departure_min: float
    halt_min: float


class TrainWithSchedule(Train):
    schedule: List[ScheduleStop] = []
