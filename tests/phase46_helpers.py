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

from phase45_helpers import make_phase45_conn
from upsert_phase46_paper_watchlist_entry import build_payload as upsert_watchlist


def make_phase46_conn() -> sqlite3.Connection:
    return make_phase45_conn()


def make_phase46_active_conn() -> sqlite3.Connection:
    conn = make_phase46_conn()
    upsert_watchlist(conn, ticker="300308.SZ", mode="execute")
    return conn
