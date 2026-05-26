#!/usr/bin/env python3
"""Phase 23 source connector registry helpers.

The registry is intentionally descriptive: planned connectors can appear in a
route, but they are never usable evidence until their status and allowed usage
say so.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from smr_paths import project_path


REGISTRY_PATH = project_path("00_control", "source_connector_registry_v2.json")
CONNECTOR_STATUSES = {"implemented", "partial", "planned", "disabled", "unavailable"}
ALLOWED_USAGES = {
    "core_evidence",
    "promotion_evidence",
    "supporting_evidence",
    "context_only",
    "planned_only",
    "blocked",
}
USABLE_STATUSES = {"implemented", "partial"}
USABLE_USAGES = {"core_evidence", "promotion_evidence", "supporting_evidence", "context_only"}


def normalize_market(market: str | None) -> str:
    raw = str(market or "").strip().upper()
    if raw in {"A", "CN", "CHINA", "SZ", "SH", "SSE", "SZSE"}:
        return "CN"
    if raw in {"H", "HK", "HKEX", "HKG"}:
        return "HK"
    if raw in {"US", "USA", "NASDAQ", "NYSE"}:
        return "US"
    return raw or "GLOBAL"


def infer_market_from_ticker(ticker: str, market: str | None = None) -> str:
    if market:
        return normalize_market(market)
    normalized = str(ticker or "").strip().upper()
    if normalized.endswith((".SZ", ".SH")):
        return "CN"
    if normalized.endswith(".HK"):
        return "HK"
    return "US"


def load_source_connector_registry(path: str | None = None) -> dict[str, Any]:
    registry_path = Path(path) if path else REGISTRY_PATH
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    return payload


def _routes_for_market(info_config: dict[str, Any], market: str) -> dict[str, Any]:
    markets = info_config.get("markets") or {}
    normalized = normalize_market(market)
    route = markets.get(normalized) or markets.get("GLOBAL") or {}
    return {
        "preferred_sources": list(route.get("preferred_sources") or []),
        "fallback_sources": list(route.get("fallback_sources") or []),
    }


def route_source_is_usable(source: dict[str, Any]) -> bool:
    status = str(source.get("status") or "")
    allowed_usage = str(source.get("allowed_usage") or "")
    return status in USABLE_STATUSES and allowed_usage in USABLE_USAGES


def route_status_for_sources(preferred_sources: list[dict[str, Any]], fallback_sources: list[dict[str, Any]]) -> str:
    sources = list(preferred_sources or []) + list(fallback_sources or [])
    if any(route_source_is_usable(source) and source.get("status") == "implemented" for source in sources):
        return "implemented"
    if any(route_source_is_usable(source) and source.get("status") == "partial" for source in sources):
        return "partial"
    if any(source.get("status") == "planned" or source.get("allowed_usage") == "planned_only" for source in sources):
        return "planned_only"
    if any(source.get("status") == "disabled" for source in sources):
        return "disabled"
    if any(source.get("status") == "unavailable" for source in sources):
        return "unavailable"
    return "missing"


def get_routes_for_information_type(
    information_type: str,
    market: str,
    *,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    registry = registry if registry is not None else load_source_connector_registry()
    info_types = registry.get("information_types") or {}
    info_config = info_types.get(str(information_type))
    normalized_market = normalize_market(market)
    if not info_config:
        return {
            "information_type": information_type,
            "market": normalized_market,
            "route_status": "UNKNOWN_INFORMATION_ROUTE",
            "preferred_sources": [],
            "fallback_sources": [],
            "next_action": "add information type to source connector registry",
        }
    route = _routes_for_market(info_config, normalized_market)
    preferred = route["preferred_sources"]
    fallback = route["fallback_sources"]
    route_status = route_status_for_sources(preferred, fallback)
    if information_type == "official_consensus" and not any(route_source_is_usable(source) for source in preferred):
        route_status = "planned_only"
    return {
        "information_type": information_type,
        "market": normalized_market,
        "description": info_config.get("description"),
        "route_status": route_status,
        "preferred_sources": preferred,
        "fallback_sources": fallback,
        "next_action": next_action_for_route(information_type, route_status, preferred, fallback),
    }


def next_action_for_route(
    information_type: str,
    route_status: str,
    preferred_sources: list[dict[str, Any]],
    fallback_sources: list[dict[str, Any]],
) -> str:
    implemented = [
        source
        for source in list(preferred_sources or []) + list(fallback_sources or [])
        if route_source_is_usable(source) and source.get("status") == "implemented"
    ]
    partial = [
        source
        for source in list(preferred_sources or []) + list(fallback_sources or [])
        if route_source_is_usable(source) and source.get("status") == "partial"
    ]
    planned = [
        source
        for source in list(preferred_sources or []) + list(fallback_sources or [])
        if source.get("status") == "planned" or source.get("allowed_usage") == "planned_only"
    ]
    if information_type == "official_consensus":
        return "commercial consensus remains planned; use internal proxy as supporting only and never label it official consensus"
    if implemented:
        connector = implemented[0].get("connector_id")
        if planned:
            return f"search implemented connector {connector} first; planned connectors remain future actions"
        return f"search implemented connector {connector} first"
    if partial:
        return f"use partial connector {partial[0].get('connector_id')} with allowed_usage={partial[0].get('allowed_usage')}"
    if planned:
        return f"planned connector {planned[0].get('connector_id')} cannot be used as evidence yet"
    return f"add source route for {information_type}"


def resolve_connector_route(
    ticker: str,
    market: str,
    information_type: str,
    *,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    route = get_routes_for_information_type(information_type, market, registry=registry)
    return {
        "ticker": str(ticker or "").strip().upper(),
        **route,
        "usable_source_count": sum(
            1 for source in route.get("preferred_sources", []) + route.get("fallback_sources", []) if route_source_is_usable(source)
        ),
        "planned_source_count": sum(
            1
            for source in route.get("preferred_sources", []) + route.get("fallback_sources", [])
            if source.get("status") == "planned" or source.get("allowed_usage") == "planned_only"
        ),
    }


def validate_connector_registry(registry: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if registry.get("version") != 2:
        issues.append({"severity": "error", "path": "version", "message": "registry version must be 2"})
    info_types = registry.get("information_types")
    if not isinstance(info_types, dict) or not info_types:
        issues.append({"severity": "error", "path": "information_types", "message": "information_types must be non-empty"})
        return issues
    for information_type, config in info_types.items():
        markets = config.get("markets") or {}
        if not markets:
            issues.append({"severity": "error", "path": information_type, "message": "information type has no market routes"})
            continue
        for market, route in markets.items():
            for bucket in ("preferred_sources", "fallback_sources"):
                for index, source in enumerate(route.get(bucket) or []):
                    path = f"{information_type}.{market}.{bucket}[{index}]"
                    for required in ("source_name", "connector_id", "status", "allowed_usage"):
                        if not source.get(required):
                            issues.append({"severity": "error", "path": path, "message": f"missing {required}"})
                    status = source.get("status")
                    allowed_usage = source.get("allowed_usage")
                    if status not in CONNECTOR_STATUSES:
                        issues.append({"severity": "error", "path": path, "message": f"invalid status {status}"})
                    if allowed_usage not in ALLOWED_USAGES:
                        issues.append({"severity": "error", "path": path, "message": f"invalid allowed_usage {allowed_usage}"})
                    if status == "planned" and allowed_usage != "planned_only":
                        issues.append({"severity": "error", "path": path, "message": "planned connector must use planned_only"})
                    if allowed_usage == "planned_only" and status != "planned":
                        issues.append({"severity": "warning", "path": path, "message": "planned_only usage should normally have planned status"})
                    if status in {"disabled", "unavailable"} and allowed_usage not in {"blocked", "planned_only"}:
                        issues.append({"severity": "warning", "path": path, "message": "disabled/unavailable connector should not be usable"})
    official = get_routes_for_information_type("official_consensus", "US", registry=registry)
    if any(source.get("status") == "implemented" for source in official.get("preferred_sources", [])):
        issues.append({"severity": "error", "path": "official_consensus", "message": "official consensus must not be implemented"})
    return issues


def summarize_connector_availability(registry: dict[str, Any]) -> dict[str, Any]:
    counts = {status: 0 for status in CONNECTOR_STATUSES}
    connector_statuses: dict[str, str] = {}
    by_information_type = []
    key_gaps = []
    for information_type, config in sorted((registry.get("information_types") or {}).items()):
        row: dict[str, Any] = {"information_type": information_type}
        for market in ("CN", "HK", "US"):
            route = get_routes_for_information_type(information_type, market, registry=registry)
            primary = (route.get("preferred_sources") or [{}])[0]
            row[market] = {
                "primary_connector": primary.get("connector_id"),
                "status": primary.get("status"),
                "allowed_usage": primary.get("allowed_usage"),
                "route_status": route.get("route_status"),
            }
        row["current_usage"] = get_routes_for_information_type(information_type, "CN", registry=registry).get("route_status")
        by_information_type.append(row)
        for market_config in (config.get("markets") or {}).values():
            for source in (market_config.get("preferred_sources") or []) + (market_config.get("fallback_sources") or []):
                connector_id = source.get("connector_id")
                if not connector_id:
                    continue
                connector_statuses.setdefault(connector_id, source.get("status") or "unavailable")
        if any((row.get(market) or {}).get("status") == "planned" for market in ("CN", "HK", "US")):
            key_gaps.append(
                {
                    "gap": information_type,
                    "current_status": "planned_or_partial",
                    "suggested_next_connector": next(
                        ((row.get(market) or {}).get("primary_connector") for market in ("CN", "HK", "US") if (row.get(market) or {}).get("status") == "planned"),
                        None,
                    ),
                }
            )
    for status in connector_statuses.values():
        if status in counts:
            counts[status] += 1
    return {
        "summary": {
            "implemented_connectors": counts.get("implemented", 0),
            "partial_connectors": counts.get("partial", 0),
            "planned_connectors": counts.get("planned", 0),
            "disabled_connectors": counts.get("disabled", 0),
            "unavailable_connectors": counts.get("unavailable", 0),
        },
        "by_information_type": by_information_type,
        "key_gaps": key_gaps,
    }
