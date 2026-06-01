import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase102_backtest_readiness.json"
    with open(p,"r",encoding="utf-8-sig") as fh: return json.load(fh)
def is_assessment_only(): return load_config()["backtest"]["assessment_only"]
def is_pnl_backtest_allowed(): return load_config()["backtest"]["pnl_backtest_allowed"]
def get_replay_periods(): return load_config()["backtest"]["replay_periods"]
