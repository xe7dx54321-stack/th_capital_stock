import json,os
from pathlib import Path
def load_config():
 p=Path(__file__).resolve().parent.parent.parent/"config"/"phase128_external_source_probe.json"
 with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
