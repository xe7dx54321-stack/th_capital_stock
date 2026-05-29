#!/usr/bin/env python3
'''Multi-ticker universe loader.'''
import json
from pathlib import Path
from typing import Any

UNIVERSE_PATH = Path(__file__).resolve().parents[2] / 'config' / 'phase69_multi_ticker_universe.json'

def load_universe() -> dict[str, Any]:
    with open(UNIVERSE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_tickers() -> list[str]:
    u = load_universe()
    return [t['ticker'] for t in u.get('tickers', [])]

def get_ticker_config(ticker: str) -> dict[str, Any]:
    u = load_universe()
    for t in u.get('tickers', []):
        if t['ticker'] == ticker:
            return t
    return {}

def get_safety() -> dict[str, Any]:
    return load_universe().get('safety', {})
