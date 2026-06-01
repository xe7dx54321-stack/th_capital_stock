import json,os
from pathlib import Path
def load_config():
 p=Path(__file__).resolve().parent.parent.parent/"config"/"phase112_opportunity_radar.json"
 with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
def is_research_only(): return load_config()["research_only"]
def is_trade_blocked(): return not load_config()["trade_recommendation_allowed"]
def get_universe(): return load_config()["universe"]