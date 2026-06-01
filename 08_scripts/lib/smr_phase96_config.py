import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase96_peer_benchmark_hard_data.json"
    with open(p,"r",encoding="utf-8-sig") as fh: return json.load(fh)
def get_universe(): return load_config()["universe"]
def get_hard_data_categories(): return load_config()["hard_data_categories"]
def get_peer_groups(): return load_config()["peer_groups"]
def get_db_path(): return load_config()["db"]["path"]
def get_field_data_types(): return load_config()["field_data_type_enum"]
