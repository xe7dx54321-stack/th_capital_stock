import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase95_300394_688041_gap_close.json"
    with open(p,"r",encoding="utf-8-sig") as f:return json.load(f)
