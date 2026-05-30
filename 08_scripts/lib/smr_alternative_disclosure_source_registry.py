#!/usr/bin/env python3
"""Phase 71: Alternative disclosure source registry."""
import json, os
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "alternative_disclosure_sources.json"

def load_registry() -> dict[str, Any]:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"sources": [], "safety": {}}

def list_sources() -> list[dict]:
    reg = load_registry()
    return reg.get("sources", [])

def get_source(source_id: str) -> dict[str, Any]:
    for s in list_sources():
        if s["source_id"] == source_id:
            return s
    return {}

def get_sources_for_market(market: str) -> list[dict]:
    return [s for s in list_sources() if s["market"] in (market, "ALL")]

def build_registry_report() -> dict[str, Any]:
    sources = list_sources()
    return {"alternative_source_registry": {"sources_count": len(sources), "sources": sources, "mock_used": False, "fixture_used": False}}
