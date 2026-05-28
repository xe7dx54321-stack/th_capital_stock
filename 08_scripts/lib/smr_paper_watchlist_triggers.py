#!/usr/bin/env python3
"""Phase 46 paper watchlist tracking trigger definitions."""

from __future__ import annotations

from typing import Any

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


TRIGGER_ROWS = [
    {
        "trigger_type": "thesis_strengthening_trigger",
        "variable": "product_mix",
        "condition": "new high-quality evidence strengthens high-end product mix",
        "resulting_status": "tracking_strengthened",
        "allowed_action": "update_tracking_status",
        "forbidden_actions": ["create_pending", "create_order", "create_trade"],
    },
    {
        "trigger_type": "thesis_weakening_trigger",
        "variable": "order_visibility",
        "condition": "order visibility weakens or demand commentary becomes less concrete",
        "resulting_status": "tracking_weakened",
        "allowed_action": "update_tracking_status",
        "forbidden_actions": ["create_trade_recommendation", "create_order", "create_trade"],
    },
    {
        "trigger_type": "evidence_update_trigger",
        "variable": "shipment",
        "condition": "new shipment or delivery evidence appears",
        "resulting_status": "tracking_needs_more_evidence",
        "allowed_action": "request_research_revalidation",
        "forbidden_actions": ["create_pending", "create_order", "create_trade"],
    },
    {
        "trigger_type": "bear_case_worsening_trigger",
        "variable": "bear_case_residual_risk",
        "condition": "bear case residual risk worsens or high-risk blocker repeats",
        "resulting_status": "tracking_weakened",
        "allowed_action": "update_tracking_status",
        "forbidden_actions": ["create_trade_recommendation", "create_order", "create_trade"],
    },
    {
        "trigger_type": "valuation_boundary_change_trigger",
        "variable": "valuation_boundary",
        "condition": "valuation boundary changes because benchmark or price/freshness support changes",
        "resulting_status": "tracking_needs_more_evidence",
        "allowed_action": "request_research_revalidation",
        "forbidden_actions": ["create_valuation_output", "create_order", "create_trade"],
    },
    {
        "trigger_type": "official_consensus_available_trigger",
        "variable": "official_consensus_status",
        "condition": "authorized consensus source metadata becomes available",
        "resulting_status": "tracking_needs_more_evidence",
        "allowed_action": "request_research_revalidation",
        "forbidden_actions": ["auto_confirm_consensus", "create_pending"],
    },
    {
        "trigger_type": "manual_review_needed_trigger",
        "variable": "supplier_share_scenario",
        "condition": "supplier share scenario receives new manual or direct-disclosure input",
        "resulting_status": "tracking_needs_more_evidence",
        "allowed_action": "request_research_revalidation",
        "forbidden_actions": ["auto_confirm_supplier_share", "create_pending", "create_order"],
    },
    {
        "trigger_type": "archive_candidate_trigger",
        "variable": "thesis_strength",
        "condition": "thesis weakens materially or tracking no longer remains research-useful",
        "resulting_status": "tracking_archived",
        "allowed_action": "archive_watchlist_entry",
        "forbidden_actions": ["create_trade_recommendation", "create_order", "create_trade"],
    },
]


def build_tracking_triggers(ticker: str = TARGET_REVIEW_TICKER) -> dict[str, Any]:
    return {
        "generated_at": now_ts(),
        "ticker": normalize_ticker(ticker),
        "tracking_triggers": [dict(row) for row in TRIGGER_ROWS],
        "safety": {
            "trigger_creates_pending": False,
            "trigger_creates_order": False,
            "trigger_creates_trade": False,
            "official_consensus_auto_confirmed": False,
        },
    }
