#!/usr/bin/env python3
"""Phase 6 watchlist configuration helpers."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from smr_paths import project_path

WATCHLIST_DIR = project_path("00_control")
DEFAULT_WATCHLIST_PATH = WATCHLIST_DIR / "phase6_ai_core_watchlist.json"


def _normalize_ticker(value: Any) -> str:
    return str(value or "").strip().upper()


@lru_cache(maxsize=8)
def load_watchlist_config(name: str = "ai_core") -> dict[str, Any]:
    path = WATCHLIST_DIR / f"phase6_{name}_watchlist.json"
    if not path.exists():
        if name != "ai_core" and DEFAULT_WATCHLIST_PATH.exists():
            path = DEFAULT_WATCHLIST_PATH
        else:
            raise FileNotFoundError(f"watchlist config not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["watchlist_id"] = payload.get("watchlist_id") or name
    payload["name"] = payload.get("name") or f"{name} watchlist"
    payload["tickers"] = [
        {
            **item,
            "ticker": _normalize_ticker(item.get("ticker")),
            "market": _normalize_ticker(item.get("market")) or item.get("market"),
            "theme": str(item.get("theme") or "").strip(),
            "sector": str(item.get("sector") or "").strip(),
            "priority": str(item.get("priority") or "medium").strip().lower(),
            "max_position_pct": float(item.get("max_position_pct") or 0.0),
            "data_requirements": [str(req).strip() for req in item.get("data_requirements") or [] if str(req).strip()],
        }
        for item in payload.get("tickers") or []
        if _normalize_ticker(item.get("ticker"))
    ]
    return payload


def watchlist_items(name: str = "ai_core") -> list[dict[str, Any]]:
    return list(load_watchlist_config(name).get("tickers") or [])


def watchlist_map(name: str = "ai_core") -> dict[str, dict[str, Any]]:
    return {item["ticker"]: item for item in watchlist_items(name)}
