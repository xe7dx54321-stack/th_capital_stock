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

from apply_phase44_manual_candidate_review_action import build_payload as apply_review
from phase43_helpers import make_phase43_conn_with_persisted


def apply_phase44_default_reviews(conn: sqlite3.Connection) -> sqlite3.Connection:
    apply_review(conn, ticker="300308.SZ", candidate_type="official_consensus", action="accept_as_candidate", mode="execute")
    apply_review(conn, ticker="300308.SZ", candidate_type="supplier_share", action="mark_as_scenario_only", mode="execute")
    apply_review(conn, ticker="300308.SZ", candidate_type="customer_allocation", action="mark_as_proxy_only", mode="execute")
    return conn


def make_phase44_closeout_conn() -> sqlite3.Connection:
    return apply_phase44_default_reviews(make_phase43_conn_with_persisted())
