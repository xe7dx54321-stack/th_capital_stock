import sqlite3, sys; from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT/"08_scripts"/"jobs",ROOT/"08_scripts"/"reporting",ROOT/"08_scripts"/"verification",ROOT/"08_scripts"/"lib",ROOT/"tests"):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
from phase49_helpers import make_phase49_active_conn
def make_phase50_conn(): return make_phase49_active_conn()
def make_phase50_active_conn(): return make_phase50_conn()
