import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase92_order_contract_tender_sources.json"
    with open(p,"r",encoding="utf-8-sig") as f:return json.load(f)
def get_universe():return load_config()["universe"]
def get_signal_types():return load_config()["signal_types"]
def get_source_types():return load_config()["source_types"]
def get_keywords(lang="cn"):return load_config()["order_keywords"][lang]
def get_ticker_entities():return load_config()["ticker_entities"]
