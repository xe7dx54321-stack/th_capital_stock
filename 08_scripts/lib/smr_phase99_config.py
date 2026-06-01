import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase99_self_healing_failover.json"
    with open(p,"r",encoding="utf-8-sig") as fh: return json.load(fh)
def get_failover_registry(): return load_config()["failover_registry"]
def is_recovery_enabled(): return load_config()["recovery"]["enabled"]
def get_recovery_history_path(): return load_config()["recovery_history"]["path"]
