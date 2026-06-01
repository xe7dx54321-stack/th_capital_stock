import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase104_human_approval_readiness.json"
    with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
def is_assessment_only(): return load_config()["human_approval"]["assessment_only"]
def get_approval_policies(): return load_config()["human_approval"]["policies"]
