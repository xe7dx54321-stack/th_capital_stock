import sqlite3, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT/"08_scripts"/"jobs", ROOT/"08_scripts"/"reporting", ROOT/"08_scripts"/"verification", ROOT/"08_scripts"/"lib", ROOT/"tests"):
    if str(p) not in sys.path: sys.path.insert(0, str(p))
from phase48_helpers import make_phase48_active_conn
def make_phase49_conn(): return make_phase48_active_conn()
def make_phase49_active_conn():
    conn = make_phase49_conn()
    from run_phase49_real_source_event_refresh import build
    build(conn, "300308.SZ", mode="execute")
    return conn
