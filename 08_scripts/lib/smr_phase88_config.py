import json
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase88_external_daily_signal_delta.json"
    with open(p,"r",encoding="utf-8-sig") as f:return json.load(f)
def get_universe():return load_config()["universe"]
def get_blocked():return load_config()["known_blocked"]
def get_directions():return load_config()["industry_directions"]
def get_signal_types():return load_config()["external_signal_types"]
def get_daily_delta_config():return load_config()["daily_delta"]
def get_source_policy():return load_config()["source_policy"]
