#!/usr/bin/env python3
"""A-share disclosure source endpoint registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ENDPOINT_REGISTRY_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "a_share_disclosure_source_endpoints.json"


def load_endpoint_registry() -> dict[str, Any]:
    """Load the endpoint registry from config JSON."""
    if not ENDPOINT_REGISTRY_PATH.exists():
        return {"sources": [], "meta": {"error": "registry file not found"}}
    with open(ENDPOINT_REGISTRY_PATH, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def get_source_by_id(source_id: str) -> dict[str, Any] | None:
    """Get a single source entry by its source_id."""
    registry = load_endpoint_registry()
    for src in registry.get("sources", []):
        if src.get("source_id") == source_id:
            return src
    return None


def get_sources_by_platform(platform: str) -> list[dict[str, Any]]:
    """Get all sources for a given platform (cninfo, szse, irm, company_site)."""
    registry = load_endpoint_registry()
    return [s for s in registry.get("sources", []) if s.get("platform") == platform]


def get_fallback_order() -> list[dict[str, Any]]:
    """Return sources sorted by fallback_priority."""
    registry = load_endpoint_registry()
    sources = [s for s in registry.get("sources", []) if s.get("fallback_priority") is not None]
    sources.sort(key=lambda s: s["fallback_priority"])
    return sources


def get_endpoint_summary() -> dict[str, Any]:
    """Build a summary of all registered endpoints."""
    registry = load_endpoint_registry()
    sources = registry.get("sources", [])
    return {
        "meta": registry.get("meta", {}),
        "total_sources": len(sources),
        "platforms": list(set(s.get("platform") for s in sources)),
        "source_ids": [s["source_id"] for s in sources],
        "raw_content_saved_all": all(s.get("raw_content_saved", False) is False for s in sources),
        "ocr_allowed_all": all(s.get("ocr_allowed", False) is False for s in sources),
        "sources": sources,
    }
