import json
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase89_unified_daily_intelligence.json"
    with open(p,"r",encoding="utf-8-sig") as f:return json.load(f)
def get_universe():return load_config()["universe"]
def get_blocked():return load_config()["known_blocked"]
def get_gaps():return load_config()["known_gaps"]
def get_subsystems():return load_config()["subsystems"]
def get_fallback_policy():return load_config()["fallback_policy"]
