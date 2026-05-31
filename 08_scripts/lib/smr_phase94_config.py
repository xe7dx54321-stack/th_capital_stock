import json,os
from pathlib import Path
def load_config():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase94_product_pricing_management_guidance.json"
    with open(p,"r",encoding="utf-8-sig") as f:return json.load(f)
def get_universe():return load_config()["universe"]
def get_pricing_signals():return load_config()["product_pricing_signal_types"]
def get_guidance_signals():return load_config()["management_guidance_signal_types"]
def get_key_products(t):return load_config().get("key_products",{}).get(t,[])
