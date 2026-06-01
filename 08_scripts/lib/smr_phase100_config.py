import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase100_continuous_production.json"
    with open(p,"r",encoding="utf-8-sig") as fh: return json.load(fh)
def get_pipeline_order(): return load_config()["production"]["pipeline_order"]
def get_reports_dir(): return load_config()["reports"]["output_dir"]
def is_reports_gitignored(): return load_config()["reports"]["gitignored"]
