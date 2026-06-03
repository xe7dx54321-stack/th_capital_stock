import json,os
from pathlib import Path
def load_config():
 p=Path(__file__).resolve().parent.parent.parent/"config"/"phase131_300394_alternative_integration.json"
 with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
