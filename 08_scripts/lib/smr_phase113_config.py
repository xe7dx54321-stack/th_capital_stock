import json,os
from pathlib import Path
def load_config():
 p=Path(__file__).resolve().parent.parent.parent/"config"/"phase113_cross_source_scoring.json"
 with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
def is_research_only(): return load_config()["research_only"]
def is_cross_source_scoring_enabled(): return load_config()["cross_source_scoring_enabled"]