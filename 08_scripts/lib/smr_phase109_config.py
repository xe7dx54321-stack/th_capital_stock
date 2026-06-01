import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase109_operator_identity_readiness.json"
    with open(p,"r",encoding="utf-8") as fh: return json.load(fh)
def is_identity_readiness_only(): return load_config()["identity"]["identity_readiness_only"]
def is_account_creation_allowed(): return load_config()["identity"]["account_creation_allowed"]
