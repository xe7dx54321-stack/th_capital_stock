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

from apply_phase40_research_review_action import build_payload as apply_phase40_action
from phase39_helpers import make_phase39_conn


def make_phase40_conn_with_action(
    *,
    action: str = "request_deeper_research",
    evidence_type: str | None = None,
) -> sqlite3.Connection:
    conn = make_phase39_conn()
    apply_phase40_action(conn, ticker="300308.SZ", action=action, evidence_type=evidence_type, mode="execute")
    return conn
