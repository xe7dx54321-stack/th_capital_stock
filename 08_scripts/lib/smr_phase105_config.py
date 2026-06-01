import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase105_kill_switch_readiness.json"
    with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
def is_assessment_only(): return load_config()["emergency_control"]["assessment_only"]
def get_safe_mode(): return load_config()["emergency_control"]["safe_mode"]
