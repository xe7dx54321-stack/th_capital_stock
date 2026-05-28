import sqlite3, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT/"08_scripts"/"jobs", ROOT/"08_scripts"/"reporting", ROOT/"08_scripts"/"verification", ROOT/"08_scripts"/"lib", ROOT/"tests"):
    if str(p) not in sys.path: sys.path.insert(0, str(p))
from phase47_helpers import make_phase47_active_conn
def make_phase48_conn(): return make_phase47_active_conn()
def make_phase48_active_conn():
    conn = make_phase48_conn()
    from run_phase48_event_evidence_refresh import build_payload
    build_payload(conn, "300308.SZ", mode="execute")
    return conn
