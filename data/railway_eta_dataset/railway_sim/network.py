"""
Static railway network reference data for the synthetic ETA dataset.

IMPORTANT: Station coordinates, distances and scheduled running times below
are APPROXIMATE / illustrative, hand-assembled for prototyping purposes.
They are good enough to produce a realistic, internally-consistent dataset
for model development and demos, but must NOT be treated as authoritative
railway data. For a production system, replace this module's contents with
official Indian Railways master data (Working Time Table, NTES station
master, RailwayBoard geo data).

Five routes are modelled to give the dataset genuine diversity, matching
the kind of variability the problem statement calls out (diverse
geographies, fog belt vs monsoon belt, congested trunk routes vs a
frequent-stop passenger corridor):

  R1  NDLS -> BCT   "Rajdhani-type" trunk route, occasional northern fog,
                     high freight+passenger congestion (Delhi-Mumbai trunk)
  R2  NDLS -> ASR   Northern fog-belt route (Punjab), fog is the dominant
                     winter risk factor
  R3  SBC  -> MAS   Southern route, low fog risk, monsoon rain sensitivity
  R4  HWH  -> NDLS  Long-distance Grand-Chord-style trunk route, heaviest
                     congestion of the five, multi-day-scale journey
  R5  MYS  -> SBC   Short frequent-stop passenger/commuter corridor, high
                     dwell-time variability, low weather sensitivity
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Station:
    code: str
    name: str
    lat: float
    lon: float


@dataclass
class Section:
    route_id: str
    seq: int  # 1-indexed position of the station THIS section arrives at
    from_code: str
    to_code: str
    distance_km: float
    scheduled_min: int          # scheduled running time for this section
    permissible_speed_kmph: int  # max sanctioned speed for this stretch
    terrain: str                 # plain | ghat | coastal | urban_approach
    fog_prone: bool
    congestion_level: float      # 0.0 (quiet) - 1.0 (very congested)
    halt_min_at_to: int          # scheduled halt at the arrival station


@dataclass
class Train:
    train_no: str
    train_name: str
    route_id: str
    train_type: str   # rajdhani_shatabdi_vb | superfast | express | passenger
    priority: int      # 1 (highest) - 5 (lowest)
    recovery_fraction: float  # fraction of section time recoverable as slack
    days_of_week: List[int]   # 0=Mon ... 6=Sun, days this train runs


STATIONS = {
    # R1: NDLS - BCT
    "NDLS": Station("NDLS", "New Delhi", 28.6431, 77.2197),
    "AGC": Station("AGC", "Agra Cantt", 27.1591, 78.0092),
    "JHS": Station("JHS", "Jhansi Jn", 25.4484, 78.5685),
    "BPL": Station("BPL", "Bhopal Jn", 23.2599, 77.4126),
    "BAU": Station("BAU", "Bhusaval Jn", 21.0433, 75.7849),
    "BCT": Station("BCT", "Mumbai Central", 18.9696, 72.8194),
    # R2: NDLS - ASR
    "UMB": Station("UMB", "Ambala Cantt", 30.3398, 76.8290),
    "JUC": Station("JUC", "Jalandhar City", 31.3260, 75.5762),
    "ASR": Station("ASR", "Amritsar Jn", 31.6340, 74.8723),
    # R3: SBC - MAS
    "SBC": Station("SBC", "Bengaluru City", 12.9767, 77.5697),
    "KPN": Station("KPN", "Katpadi Jn", 12.9698, 79.1364),
    "JTJ": Station("JTJ", "Jolarpettai Jn", 12.5762, 78.5730),
    "MAS": Station("MAS", "Chennai Central", 13.0827, 80.2707),
    # R4: HWH - NDLS
    "HWH": Station("HWH", "Howrah Jn", 22.5851, 88.3468),
    "DHN": Station("DHN", "Dhanbad Jn", 23.7957, 86.4304),
    "GAYA": Station("GAYA", "Gaya Jn", 24.7955, 84.9994),
    "DDU": Station("DDU", "Pt Deen Dayal Upadhyaya Jn", 25.2803, 83.1259),
    "CNB": Station("CNB", "Kanpur Central", 26.4499, 80.3319),
    # R5: MYS - SBC
    "MYS": Station("MYS", "Mysuru Jn", 12.3072, 76.6553),
    "SRGN": Station("SRGN", "Srirangapatna", 12.4192, 76.6936),
    "MYA": Station("MYA", "Mandya", 12.5237, 76.8974),
    "CPT": Station("CPT", "Channapatna", 12.6514, 77.2065),
    "RRB": Station("RRB", "Ramanagara", 12.7217, 77.2818),
}

# (route_id, from, to, distance_km, scheduled_min, permissible_speed,
#  terrain, fog_prone, congestion_level, halt_min_at_to)
_RAW_SECTIONS = [
    # R1 NDLS -> BCT (Rajdhani-type, ~1384 km, avg ~80 km/h schedule)
    ("R1", "NDLS", "AGC", 200, 150, 130, "plain", True, 0.55, 2),
    ("R1", "AGC", "JHS", 200, 145, 120, "plain", True, 0.45, 5),
    ("R1", "JHS", "BPL", 300, 210, 110, "plain", False, 0.40, 5),
    ("R1", "BPL", "BAU", 400, 280, 100, "plain", False, 0.50, 5),
    ("R1", "BAU", "BCT", 284, 220, 100, "ghat", False, 0.65, 0),
    # R2 NDLS -> ASR (fog belt, ~449 km)
    ("R2", "NDLS", "UMB", 200, 160, 110, "plain", True, 0.35, 5),
    ("R2", "UMB", "JUC", 200, 165, 100, "plain", True, 0.30, 5),
    ("R2", "JUC", "ASR", 49, 50, 90, "plain", True, 0.25, 0),
    # R3 SBC -> MAS (low fog, monsoon sensitive, ~362 km)
    ("R3", "SBC", "KPN", 214, 160, 110, "plain", False, 0.30, 3),
    ("R3", "KPN", "JTJ", 36, 35, 100, "plain", False, 0.20, 3),
    ("R3", "JTJ", "MAS", 112, 95, 110, "coastal", False, 0.35, 0),
    # R4 HWH -> NDLS (Grand-Chord-style trunk, ~1447 km, most congested)
    ("R4", "HWH", "DHN", 260, 220, 90, "plain", False, 0.70, 10),
    ("R4", "DHN", "GAYA", 160, 150, 90, "plain", False, 0.60, 5),
    ("R4", "GAYA", "DDU", 150, 140, 90, "plain", False, 0.55, 10),
    ("R4", "DDU", "CNB", 320, 260, 100, "plain", True, 0.60, 5),
    ("R4", "CNB", "NDLS", 440, 320, 110, "plain", True, 0.65, 0),
    # R5 MYS -> SBC (frequent-stop passenger corridor, ~139 km)
    ("R5", "MYS", "SRGN", 15, 20, 70, "urban_approach", False, 0.20, 2),
    ("R5", "SRGN", "MYA", 31, 35, 80, "plain", False, 0.20, 2),
    ("R5", "MYA", "CPT", 41, 45, 80, "plain", False, 0.25, 2),
    ("R5", "CPT", "RRB", 10, 15, 70, "plain", False, 0.25, 2),
    ("R5", "RRB", "SBC", 42, 55, 90, "urban_approach", False, 0.45, 0),
]


def build_sections() -> List[Section]:
    sections = []
    seq_counter = {}
    for (rid, f, t, dist, sched, perm, terr, fog, cong, halt) in _RAW_SECTIONS:
        seq_counter[rid] = seq_counter.get(rid, 0) + 1
        sections.append(Section(rid, seq_counter[rid], f, t, dist, sched,
                                 perm, terr, fog, cong, halt))
    return sections


SECTIONS = build_sections()

ROUTE_ORIGIN = {
    "R1": "NDLS", "R2": "NDLS", "R3": "SBC", "R4": "HWH", "R5": "MYS",
}

TRAINS = [
    Train("12951", "Mumbai Rajdhani Express", "R1", "rajdhani_shatabdi_vb", 1, 0.12, list(range(7))),
    Train("19269", "Bandra Superfast Express", "R1", "superfast", 2, 0.08, [0, 2, 4]),
    Train("12459", "Swarna Shatabdi (NDLS-ASR)", "R2", "rajdhani_shatabdi_vb", 1, 0.10, list(range(7))),
    Train("14673", "Amritsar Superfast Express", "R2", "superfast", 2, 0.07, [1, 3, 5, 6]),
    Train("12007", "Shatabdi Express (SBC-MAS)", "R3", "rajdhani_shatabdi_vb", 1, 0.10, list(range(7))),
    Train("16021", "Kaveri Express", "R3", "express", 3, 0.06, list(range(7))),
    Train("12302", "Howrah Rajdhani Express", "R4", "rajdhani_shatabdi_vb", 1, 0.10, list(range(7))),
    Train("13005", "Amritsar Mail (via Grand Chord)", "R4", "express", 3, 0.05, list(range(7))),
    Train("56215", "Mysuru-Bengaluru Passenger", "R5", "passenger", 5, 0.03, list(range(7))),
    Train("06231", "Mysuru-Bengaluru MEMU Special", "R5", "passenger", 5, 0.03, list(range(7))),
]


def sections_for_route(route_id: str) -> List[Section]:
    return [s for s in SECTIONS if s.route_id == route_id]


def trains_for_route(route_id: str) -> List[Train]:
    return [t for t in TRAINS if t.route_id == route_id]
