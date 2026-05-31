import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase93_customer_capex_supply_chain_sources.json"
    with open(p,"r",encoding="utf-8-sig") as f:return json.load(f)
def get_universe():return load_config()["universe"]
def get_customer_signals():return load_config()["customer_capex_signal_types"]
def get_supply_signals():return load_config()["supply_chain_signal_types"]
def get_linkage_signals():return load_config()["linkage_signal_types"]
def get_key_customers(t):return load_config().get("key_customers",{}).get(t,[])
def get_key_suppliers(t):return load_config().get("key_suppliers",{}).get(t,[])
