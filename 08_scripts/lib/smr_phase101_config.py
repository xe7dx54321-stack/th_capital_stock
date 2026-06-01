import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase101_live_trading_readiness.json"
    with open(p,"r",encoding="utf-8-sig") as fh: return json.load(fh)
def is_assessment_only(): return load_config()["assessment"]["assessment_only"]
def is_live_trading_enabled(): return load_config()["assessment"]["live_trading_enabled"]
def get_readiness_domains(): return load_config()["readiness_domains"]
