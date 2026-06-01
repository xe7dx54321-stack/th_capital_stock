import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase108_paper_execution_readiness.json"
    with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
def is_readiness_only(): return load_config()["paper_execution"]["readiness_only"]
def is_paper_execution_enabled(): return load_config()["paper_execution"]["paper_execution_enabled"]
