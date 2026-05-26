#!/usr/bin/env python3
"""Build source acquisition plans from repair tasks and blocker routes."""

from __future__ import annotations

from typing import Any

from smr_blocker_source_router import build_source_routes_for_blocker, load_blocker_source_route_map, map_blocker_to_information_types
from smr_source_connector_registry import normalize_market, route_source_is_usable


STATUS_RANK = {"implemented": 0, "partial": 1, "planned": 2, "disabled": 3, "unavailable": 4}
USAGE_RANK = {"core_evidence": 0, "promotion_evidence": 1, "supporting_evidence": 2, "context_only": 3, "planned_only": 4, "blocked": 5}


def _source_action(information_type: str, source: dict[str, Any]) -> str:
    connector_id = source.get("connector_id")
    status = source.get("status")
    allowed_usage = source.get("allowed_usage")
    if status == "planned" or allowed_usage == "planned_only":
        return f"planned connector for {information_type}; do not execute or write evidence yet"
    if allowed_usage == "context_only":
        return f"search {connector_id} for context only; do not use as promotion evidence"
    if information_type == "official_consensus":
        return "commercial consensus route is planned; internal proxy fallback remains supporting only"
    return f"search {connector_id} for {information_type} evidence"


def _ordered_sources(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for route in routes:
        information_type = route.get("information_type")
        for bucket in ("preferred_sources", "fallback_sources"):
            bucket_rank = 0 if bucket == "preferred_sources" else 1
            for source in route.get(bucket) or []:
                key = (str(source.get("connector_id")), str(information_type), str(source.get("allowed_usage")))
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "information_type": information_type,
                        "connector_id": source.get("connector_id"),
                        "source_name": source.get("source_name"),
                        "status": source.get("status"),
                        "allowed_usage": source.get("allowed_usage"),
                        "source_quality": source.get("source_quality"),
                        "evidence_category": source.get("evidence_category"),
                        "is_usable_now": route_source_is_usable(source),
                        "action": _source_action(str(information_type), source),
                        "_sort": (
                            STATUS_RANK.get(str(source.get("status")), 99),
                            bucket_rank,
                            USAGE_RANK.get(str(source.get("allowed_usage")), 99),
                            str(source.get("connector_id")),
                        ),
                    }
                )
    rows.sort(key=lambda row: row["_sort"])
    ordered = []
    for index, row in enumerate(rows, start=1):
        clean = {key: value for key, value in row.items() if key != "_sort"}
        clean["step"] = index
        ordered.append(clean)
    return ordered


def build_source_acquisition_plan_for_task(
    task: dict[str, Any],
    *,
    ticker: str,
    market: str,
    registry: dict[str, Any] | None = None,
    route_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    route_map = route_map if route_map is not None else load_blocker_source_route_map()
    raw_task_type = str(task.get("task_type") or task.get("blocker_code") or task.get("missing_evidence") or "")
    missing_evidence = str(task.get("missing_evidence") or raw_task_type)
    task_type = raw_task_type
    if missing_evidence.upper() in route_map:
        task_type = missing_evidence.upper()
    information_types = map_blocker_to_information_types(task_type, route_map=route_map)
    route_bundle = build_source_routes_for_blocker(task_type, ticker, market, route_map=route_map, registry=registry)
    routes = route_bundle.get("source_routes") or []
    steps = _ordered_sources(routes)
    next_action = steps[0]["action"] if steps else "add source route before acquisition"
    return {
        "repair_task_type": task_type,
        "priority": task.get("priority") or route_bundle.get("priority") or "medium",
        "missing_evidence": missing_evidence,
        "source_acquisition_plan": {
            "information_types": information_types,
            "market": normalize_market(market),
            "ordered_steps": steps,
            "next_action": next_action,
            "planned_connectors_executed": False,
            "writes_evidence_graph": False,
        },
    }


def build_source_acquisition_plan_for_blocker(
    blocker_code: str,
    *,
    ticker: str,
    market: str,
    registry: dict[str, Any] | None = None,
    route_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return build_source_acquisition_plan_for_task(
        {"task_type": blocker_code, "missing_evidence": blocker_code},
        ticker=ticker,
        market=market,
        registry=registry,
        route_map=route_map,
    )
