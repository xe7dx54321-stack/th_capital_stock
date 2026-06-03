import json,os
from pathlib import Path
def load_config():
 p=Path(__file__).resolve().parent.parent.parent/"config"/"phase135_owner_feedback_integration.json"
 with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
