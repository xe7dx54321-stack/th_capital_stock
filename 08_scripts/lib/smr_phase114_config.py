import json,os
from pathlib import Path
def load_config():
 p=Path(__file__).resolve().parent.parent.parent/"config"/"phase114_catalyst_inflection_detector.json"
 with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
def is_research_only(): return load_config()["research_only"]
def is_catalyst_enabled(): return load_config()["catalyst_detection_enabled"]