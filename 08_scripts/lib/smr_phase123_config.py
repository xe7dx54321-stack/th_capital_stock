import json,os
from pathlib import Path
def load_config():
 p=Path(__file__).resolve().parent.parent.parent/"config"/"phase123_owner_feedback_memory.json"
 with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
