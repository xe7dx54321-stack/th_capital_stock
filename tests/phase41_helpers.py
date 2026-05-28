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

from execute_phase41_specific_evidence_requests import build_payload as execute_specific_requests
from phase40_helpers import make_phase40_conn_with_action


def make_phase41_conn_with_followups() -> sqlite3.Connection:
    conn = make_phase40_conn_with_action(action="request_deeper_research")
    execute_specific_requests(conn, ticker="300308.SZ", mode="execute")
    return conn
