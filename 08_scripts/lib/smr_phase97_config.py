import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase97_automated_db_refresh.json"
    with open(p,"r",encoding="utf-8-sig") as fh: return json.load(fh)
def get_refresh_policy(): return load_config()["source_refresh_policy"]
def get_db_paths(): return load_config()["db"]
def get_stale_days(): return load_config()["refresh"]["stale_days_before_stale"]
def is_dedup_enabled(): return load_config()["dedup"]["enabled"]
