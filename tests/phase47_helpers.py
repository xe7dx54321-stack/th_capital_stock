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

from phase46_helpers import make_phase46_active_conn
from run_phase47_periodic_watchlist_review import build_payload as execute_review


def make_phase47_conn() -> sqlite3.Connection:
    return make_phase46_active_conn()


def make_phase47_active_conn() -> sqlite3.Connection:
    conn = make_phase47_conn()
    execute_review(conn, ticker="300308.SZ", mode="execute")
    return conn
