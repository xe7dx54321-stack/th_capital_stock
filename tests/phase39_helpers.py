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

from persist_phase38_300308_targeted_candidates import build_payload as persist_candidates
from phase38_helpers import make_phase38_conn
from upsert_phase38_300394_repair_tasks import build_payload as upsert_repair


def make_phase39_conn(*, with_repair: bool = True) -> sqlite3.Connection:
    conn = make_phase38_conn()
    persist_candidates(conn, mode="execute", limit=5)
    if with_repair:
        upsert_repair(conn, mode="execute")
    return conn
