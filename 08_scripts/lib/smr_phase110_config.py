import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase110_operator_assignment_manifest.json"
    with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
def is_manual_assignment_only(): return load_config()["assignment"]["manual_assignment_only"]
