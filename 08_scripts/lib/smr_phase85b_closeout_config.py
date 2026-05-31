import json
from pathlib import Path

def load_config():
    p = Path(__file__).resolve().parent.parent.parent / "config" / "phase85b_valuation_source_hardening_closeout.json"
    with open(p, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def get_problem_tickers():
    c = load_config()
    return c["problem_tickers"]

def get_preserved_blocked():
    c = load_config()
    return c["preserved_blocked"]

def get_ticker_format_map():
    c = load_config()
    return c["ticker_format_map"]

def get_derived_config():
    c = load_config()
    return c["derived_valuation"]

def get_proxy_pairs():
    c = load_config()
    return c["proxy"]["pairs"]
