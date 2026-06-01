import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase106_readiness_integration.json"
    with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
def is_assessment_only(): return load_config()["integration"]["assessment_only"]
def get_modules(): return load_config()["integration"]["modules"]
