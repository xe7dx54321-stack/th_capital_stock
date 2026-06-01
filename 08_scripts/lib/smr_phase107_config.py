import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase107_paper_trading_boundary.json"
    with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
def is_boundary_only(): return load_config()["paper_trading"]["boundary_definition_only"]
def is_paper_trading_enabled(): return load_config()["paper_trading"]["paper_trading_enabled"]
