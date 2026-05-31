import json
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase91_information_source_reality_audit.json"
    with open(p,"r",encoding="utf-8-sig") as f:return json.load(f)
def get_universe():return load_config()["universe"]
def get_dimensions():return load_config()["information_dimensions"]
def get_taxonomy():return load_config()["source_classification_taxonomy"]
def get_known_blocked():return load_config()["known_blocked"]
def get_known_gaps():return load_config()["known_gaps"]
def get_audit_scope():return load_config()["audit_scope"]
