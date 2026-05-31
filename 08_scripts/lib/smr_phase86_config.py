import json
from pathlib import Path

def load_config():
    p = Path(__file__).resolve().parent.parent.parent / "config" / "phase86_expectation_market_pricing.json"
    with open(p, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def get_target_tickers():
    return load_config()["target_tickers"]

def get_known_blocked():
    return load_config()["known_blocked"]

def get_pricing_sources(market):
    return load_config()["pricing"]["sources"].get(market, [])

def get_ticker_format(ticker):
    return load_config()["pricing"]["ticker_format_map"].get(ticker, ticker)

def get_expectation_sources(market):
    return load_config()["expectation"]["sources"].get(market, [])

def get_indices():
    return load_config()["pricing"]["indices"]
