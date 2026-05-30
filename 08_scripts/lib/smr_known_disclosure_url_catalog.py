#!/usr/bin/env python3
"""Phase 71: Known disclosure URL catalog."""
import json
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "known_disclosure_url_catalog.json"

def load_catalog() -> dict[str, Any]:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"catalog": []}

def get_urls_for_ticker(ticker: str) -> list[dict]:
    cat = load_catalog()
    return [c for c in cat.get("catalog", []) if c["ticker"] == ticker]

def get_available_urls(ticker: str) -> list[dict]:
    """Only return URLs that are not manual_fill_required."""
    return [c for c in get_urls_for_ticker(ticker) if c.get("url") and c.get("url_status") != "manual_fill_required"]

def build_catalog_report() -> dict[str, Any]:
    cat = load_catalog()
    entries = cat.get("catalog", [])
    available = sum(1 for c in entries if c.get("url_status") != "manual_fill_required" and c.get("url"))
    manual = sum(1 for c in entries if c.get("url_status") == "manual_fill_required")
    return {"known_url_catalog": {"entries_total": len(entries), "available": available, "manual_fill_required": manual, "entries": entries, "mock_used": False, "fixture_used": False}}
