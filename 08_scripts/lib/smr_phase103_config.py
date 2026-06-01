import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase103_risk_control_readiness.json"
    with open(p,"r",encoding="utf-8-sig") as fh: return json.load(fh)
def is_live_risk_enabled(): return load_config()["risk_control"]["live_risk_execution_enabled"]
def get_risk_rules(): return load_config()["risk_control"]["rules"]
