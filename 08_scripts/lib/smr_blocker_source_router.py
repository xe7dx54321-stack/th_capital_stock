#!/usr/bin/env python3
"""Map gate blockers to source connector routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from smr_paths import project_path
from smr_source_connector_registry import normalize_market, resolve_connector_route


ROUTE_MAP_PATH = project_path("00_control", "blocker_source_route_map.json")


def load_blocker_source_route_map(path: str | None = None) -> dict[str, Any]:
    route_path = Path(path) if path else ROUTE_MAP_PATH
    return json.loads(route_path.read_text(encoding="utf-8"))


def normalize_blocker_code(blocker_code: str | None) -> str:
    return str(blocker_code or "").strip().upper()


def map_blocker_to_information_types(blocker_code: str, *, route_map: dict[str, Any] | None = None) -> list[str]:
    route_map = route_map if route_map is not None else load_blocker_source_route_map()
    code = normalize_blocker_code(blocker_code)
    item = route_map.get(code)
    if item:
        return [str(value) for value in item.get("information_types") or [] if str(value)]
    return ["UNKNOWN_INFORMATION_ROUTE"]


def blocker_priority(blocker_code: str, *, route_map: dict[str, Any] | None = None) -> str:
    route_map = route_map if route_map is not None else load_blocker_source_route_map()
    return str((route_map.get(normalize_blocker_code(blocker_code)) or {}).get("priority") or "medium")


def build_source_routes_for_blocker(
    blocker_code: str,
    ticker: str,
    market: str,
    *,
    route_map: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    route_map = route_map if route_map is not None else load_blocker_source_route_map()
    code = normalize_blocker_code(blocker_code)
    mapping = route_map.get(code)
    information_types = map_blocker_to_information_types(code, route_map=route_map)
    source_routes = []
    for information_type in information_types:
        if information_type == "UNKNOWN_INFORMATION_ROUTE":
            source_routes.append(
                {
                    "blocker_code": code,
                    "information_type": information_type,
                    "route_status": "UNKNOWN_INFORMATION_ROUTE",
                    "preferred_sources": [],
                    "fallback_sources": [],
                    "next_action": "add blocker to blocker_source_route_map.json",
                }
            )
            continue
        route = resolve_connector_route(ticker, market, information_type, registry=registry)
        source_routes.append(
            {
                "blocker_code": code,
                "information_type": information_type,
                "route_status": route.get("route_status"),
                "preferred_sources": route.get("preferred_sources") or [],
                "fallback_sources": route.get("fallback_sources") or [],
                "next_action": route.get("next_action"),
                "usable_source_count": route.get("usable_source_count"),
                "planned_source_count": route.get("planned_source_count"),
            }
        )
    return {
        "blocker_code": code,
        "ticker": str(ticker or "").strip().upper(),
        "market": normalize_market(market),
        "priority": str((mapping or {}).get("priority") or "medium"),
        "reason": str((mapping or {}).get("reason") or "No source route mapping is configured."),
        "information_types": information_types,
        "source_routes": source_routes,
        "has_source_route": all(route.get("route_status") != "UNKNOWN_INFORMATION_ROUTE" for route in source_routes),
    }
