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

from build_phase43_manual_intake_candidates import build_payload as build_candidates
from persist_phase43_manual_intake_candidates import build_payload as persist_candidates
from phase42_helpers import make_phase42_conn


def make_phase43_conn_with_candidates() -> sqlite3.Connection:
    conn = make_phase42_conn()
    build_candidates(conn, ticker="300308.SZ", mode="execute")
    return conn


def make_phase43_conn_with_persisted() -> sqlite3.Connection:
    conn = make_phase43_conn_with_candidates()
    persist_candidates(conn, ticker="300308.SZ", mode="execute")
    return conn


def make_phase43_conn_with_rejection() -> sqlite3.Connection:
    conn = make_phase42_conn()
    build_candidates(conn, ticker="300308.SZ", sample="bad_consensus_internal_proxy", mode="execute")
    return conn
