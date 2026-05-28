import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (
    ROOT / "08_scripts" / "jobs",
    ROOT / "08_scripts" / "reporting",
    ROOT / "08_scripts" / "verification",
    ROOT / "08_scripts" / "lib",
    ROOT / "tests",
):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase41_helpers import make_phase41_conn_with_followups


def make_phase42_conn() -> sqlite3.Connection:
    return make_phase41_conn_with_followups()
