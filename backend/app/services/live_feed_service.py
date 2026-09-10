"""
Wraps live_feed_simulator.py (from the dataset package) so the backend can
stream a "live" journey to the frontend. This is what makes the frontend's
ETA page feel live during development/demo, before a real RTIS/COA feed
exists.

TODO(Antigravity): the dataset package's live_feed_simulator.py must be on
the Python path for this import to work — it's imported dynamically here
via sys.path manipulation rather than a normal package import, since the
dataset package lives in data/railway_eta_dataset/ rather than inside
backend/. Once you restructure for production, consider moving
railway_sim/ into a proper shared Python package installed via
requirements.txt (`pip install -e ./data/railway_eta_dataset`) instead.
"""

import sys
from datetime import date, datetime

from app.core.config import settings

_dataset_pkg = str(settings.DATASET_PKG_DIR)
if _dataset_pkg not in sys.path:
    sys.path.insert(0, _dataset_pkg)


def stream_journey_events(train_no: str, journey_date_str: str, seed: int = None):
    """Generator yielding dict events for one journey. See
    live_feed_simulator.simulate_journey_events for the event shapes
    (departure / position / arrival)."""
    from live_feed_simulator import simulate_journey_events  # dataset package

    jdate = datetime.strptime(journey_date_str, "%Y-%m-%d").date()
    yield from simulate_journey_events(train_no, jdate, seed=seed)
