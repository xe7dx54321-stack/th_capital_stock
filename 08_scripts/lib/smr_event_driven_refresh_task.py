#!/usr/bin/env python3
"""Phase 48 event-driven evidence refresh task generation."""

from __future__ import annotations

from typing import Any

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_watchlist_event_trigger import FORBIDDEN_ACTIONS
from smr_wiki import generate_execution_id, now_ts


TASK_TYPES = {
    "REFRESH_IR_TEXT",
    "REFRESH_ANNOUNCEMENT_METADATA",
    "REFRESH_EVIDENCE_CHAIN",
    "REFRESH_TRACKING_VARIABLE",
    "REFRESH_MANUAL_CANDIDATE_STATUS",
    "REFRESH_BEAR_CASE",
    "REFRESH_VALUATION_BOUNDARY",
    "REVALIDATE_THESIS",
    "NOOP",
}

VARIABLE_TO_TASK = {
    "product_mix": "REFRESH_TRACKING_VARIABLE",
    "order_visibility": "REFRESH_TRACKING_VARIABLE",
    "shipment": "REFRESH_TRACKING_VARIABLE",
    "ASP_price_proxy": "REFRESH_TRACKING_VARIABLE",
    "supplier_share_scenario": "REFRESH_TRACKING_VARIABLE",
    "official_consensus_status": "REFRESH_TRACKING_VARIABLE",
    "customer_allocation_proxy": "REFRESH_TRACKING_VARIABLE",
    "bear_case_residual_risk": "REFRESH_BEAR_CASE",
    "valuation_boundary": "REFRESH_VALUATION_BOUNDARY",
    "evidence_quality": "REFRESH_EVIDENCE_CHAIN",
    "thesis_strength": "REVALIDATE_THESIS",
}

EVENT_TYPE_TO_TASK = {
    "investor_relations_record": "REFRESH_TRACKING_VARIABLE",
    "new_ir_text": "REFRESH_TRACKING_VARIABLE",
    "earnings_report": "REVALIDATE_THESIS",
    "major_announcement": "REFRESH_TRACKING_VARIABLE",
    "new_evidence_candidate": "REFRESH_EVIDENCE_CHAIN",
    "bear_case_change": "REFRESH_BEAR_CASE",
    "valuation_boundary_change": "REFRESH_VALUATION_BOUNDARY",
}


def generate_refresh_tasks(
    events: list[dict[str, Any]],
    ticker: str = TARGET_REVIEW_TICKER,
) -> list[dict[str, Any]]:
    ticker = normalize_ticker(ticker)
    tasks: list[dict[str, Any]] = []
    for event in events:
        if not event.get("requires_evidence_refresh"):
            continue
        event_id = event.get("event_id", "")
        event_type = event.get("event_type", "")
        variables = event.get("linked_tracking_variables", [])
        task_type = EVENT_TYPE_TO_TASK.get(event_type)
        for var in variables:
            tt = task_type or VARIABLE_TO_TASK.get(var, "REFRESH_TRACKING_VARIABLE")
            if tt == "NOOP":
                continue
            tasks.append({
                "task_id": generate_execution_id(f"refresh_task_{ticker.split('.')[0]}_phase48"),
                "event_id": event_id,
                "task_type": tt,
                "target_variable": var,
                "priority": event.get("event_strength", "medium"),
                "execution_mode": "dry_run_first",
                "allowed_action": "research_only_refresh",
                "forbidden_actions": list(FORBIDDEN_ACTIONS),
            })
    return tasks


def build_event_refresh_tasks(
    events: list[dict[str, Any]],
    ticker: str = TARGET_REVIEW_TICKER,
) -> dict[str, Any]:
    tasks = generate_refresh_tasks(events, ticker)
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "event_refresh_tasks": {
            "tasks_generated": len(tasks),
            "research_only_tasks": len(tasks),
            "tasks": tasks,
            "pending_created": 0,
            "paper_order_created": 0,
        },
        "safety": {
            "tasks_creates_pending": False,
            "tasks_creates_order": False,
            "tasks_are_research_only": True,
        },
    }
