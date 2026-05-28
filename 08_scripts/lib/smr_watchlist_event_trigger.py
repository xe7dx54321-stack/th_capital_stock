#!/usr/bin/env python3
"""Phase 48 watchlist event trigger schema and persistence."""

from __future__ import annotations

from typing import Any

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import generate_execution_id, now_ts


EVENT_TYPES = {
    "earnings_report",
    "earnings_preview",
    "major_announcement",
    "investor_relations_record",
    "new_ir_text",
    "new_evidence_candidate",
    "manual_candidate_update",
    "official_consensus_status_change",
    "supplier_share_scenario_update",
    "customer_allocation_proxy_update",
    "bear_case_change",
    "valuation_boundary_change",
    "tracking_variable_change",
    "periodic_review_due",
    "unknown",
}

EVENT_STRENGTHS = {"low", "medium", "high"}

FORBIDDEN_ACTIONS = [
    "create_pending",
    "create_paper_order",
    "create_trade",
]

SAMPLE_EVENTS = [
    {
        "ticker": "300308.SZ",
        "event_type": "investor_relations_record",
        "event_source": "existing_source_or_sample_fixture",
        "event_title": "Sample IR update related to product mix",
        "linked_tracking_variables": ["product_mix", "order_visibility"],
        "event_strength": "medium",
    },
    {
        "ticker": "300308.SZ",
        "event_type": "periodic_review_due",
        "event_source": "phase47_periodic_review",
        "event_title": "Periodic review scheduled",
        "linked_tracking_variables": ["thesis_strength"],
        "event_strength": "low",
    },
]


def build_event_trigger(
    ticker: str = TARGET_REVIEW_TICKER,
    event_type: str = "unknown",
    event_source: str = "",
    event_title: str = "",
    linked_tracking_variables: list[str] | None = None,
    event_strength: str = "medium",
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    if event_type not in EVENT_TYPES:
        event_type = "unknown"
    if event_strength not in EVENT_STRENGTHS:
        event_strength = "medium"
    linked = linked_tracking_variables or []
    requires_refresh = event_type not in {"unknown", "periodic_review_due"}
    requires_revalidation = event_type not in {"unknown", "periodic_review_due"}
    event_id = generate_execution_id(f"watchlist_event_{ticker.split('.')[0]}_phase48")
    return {
        "ticker": ticker,
        "event_id": event_id,
        "event_type": event_type,
        "event_source": event_source,
        "event_title": event_title,
        "event_date": now_ts(),
        "linked_tracking_variables": linked,
        "event_strength": event_strength,
        "requires_evidence_refresh": requires_refresh,
        "requires_revalidation": requires_revalidation,
        "allowed_action": "research_only_revalidation",
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "pending_created": False,
        "paper_order_created": False,
        "real_trade_created": False,
    }
