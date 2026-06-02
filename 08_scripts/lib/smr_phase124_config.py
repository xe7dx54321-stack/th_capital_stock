import json,os
from pathlib import Path
def load_config():
 p=Path(__file__).resolve().parent.parent.parent/"config"/"phase124_decision_journal.json"
 with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
