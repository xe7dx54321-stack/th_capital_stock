#!/usr/bin/env python3
"""Phase 46 tracking variables for paper watchlist entries."""

from __future__ import annotations

from typing import Any

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


TRACKING_VARIABLE_ROWS = [
    {
        "variable": "product_mix",
        "current_status": "supported",
        "tracking_goal": "watch whether high-end optical product mix evidence continues to strengthen",
        "strengthening_signal": "new company disclosure or IR commentary supports high-end mix",
        "weakening_signal": "company commentary suggests product mix pressure or demand slowdown",
        "update_frequency": "weekly_or_on_new_evidence",
        "allowed_usage": "research_tracking",
    },
    {
        "variable": "order_visibility",
        "current_status": "partially_supported",
        "tracking_goal": "watch whether order visibility becomes more concrete",
        "strengthening_signal": "new disclosure gives clearer backlog, delivery, or demand visibility",
        "weakening_signal": "order commentary becomes vague, delayed, or demand visibility weakens",
        "update_frequency": "weekly_or_on_new_evidence",
        "allowed_usage": "research_tracking",
    },
    {
        "variable": "shipment",
        "current_status": "supported",
        "tracking_goal": "watch whether shipment evidence continues to support thesis",
        "strengthening_signal": "new evidence supports shipment growth or delivery cadence",
        "weakening_signal": "shipment cadence slows or customer demand commentary weakens",
        "update_frequency": "weekly_or_on_new_evidence",
        "allowed_usage": "research_tracking",
    },
    {
        "variable": "ASP_price_proxy",
        "current_status": "partially_supported",
        "tracking_goal": "watch whether ASP or high-end pricing proxy improves",
        "strengthening_signal": "new evidence supports better product ASP or mix-driven pricing",
        "weakening_signal": "pricing pressure or mix-down evidence appears",
        "update_frequency": "weekly_or_on_new_evidence",
        "allowed_usage": "research_tracking_only",
    },
    {
        "variable": "supplier_share_scenario",
        "current_status": "scenario_only",
        "tracking_goal": "watch whether supplier share remains scenario-only or receives direct support",
        "strengthening_signal": "direct public disclosure supports supplier share assumption",
        "weakening_signal": "scenario remains unsupported or contradictory public evidence appears",
        "update_frequency": "manual_or_on_source_update",
        "allowed_usage": "scenario_tracking_only",
    },
    {
        "variable": "official_consensus_status",
        "current_status": "unconfirmed",
        "tracking_goal": "watch whether authorized consensus source becomes available",
        "strengthening_signal": "authorized source metadata provided",
        "weakening_signal": "no authorized source after review cycle",
        "update_frequency": "manual_or_on_source_update",
        "allowed_usage": "research_tracking_only",
    },
    {
        "variable": "customer_allocation_proxy",
        "current_status": "proxy_only",
        "tracking_goal": "watch whether proxy evidence becomes direct customer allocation evidence",
        "strengthening_signal": "company or customer-side public statement directly supports allocation",
        "weakening_signal": "proxy remains generic or customer references become less specific",
        "update_frequency": "manual_or_on_source_update",
        "allowed_usage": "proxy_tracking_only",
    },
    {
        "variable": "bear_case_residual_risk",
        "current_status": "partially_mitigated_not_cleared",
        "tracking_goal": "watch whether residual risk improves or worsens",
        "strengthening_signal": "new evidence mitigates remaining demand, allocation, or valuation risks",
        "weakening_signal": "bear case evidence worsens or high-risk blocker repeats",
        "update_frequency": "weekly_or_on_new_evidence",
        "allowed_usage": "risk_tracking",
    },
    {
        "variable": "valuation_boundary",
        "current_status": "scenario_analysis_only",
        "tracking_goal": "watch whether valuation boundary becomes less scenario-bound",
        "strengthening_signal": "authorized benchmark or stronger valuation support appears",
        "weakening_signal": "valuation support remains partial or price/freshness blockers persist",
        "update_frequency": "weekly_or_on_new_evidence",
        "allowed_usage": "research_tracking_only",
    },
    {
        "variable": "evidence_quality",
        "current_status": "watchlist_sufficient_not_pending_sufficient",
        "tracking_goal": "watch whether evidence quality improves enough for revalidation",
        "strengthening_signal": "new high-quality company-specific evidence links to core variables",
        "weakening_signal": "new evidence is low quality, stale, or not company specific",
        "update_frequency": "weekly_or_on_new_evidence",
        "allowed_usage": "research_tracking",
    },
    {
        "variable": "thesis_strength",
        "current_status": "watchlist_positive_but_unconfirmed",
        "tracking_goal": "watch whether thesis strength improves or deteriorates",
        "strengthening_signal": "multiple tracked variables strengthen without adding new blockers",
        "weakening_signal": "bear case worsens or key tracked variables weaken",
        "update_frequency": "weekly_or_on_new_evidence",
        "allowed_usage": "research_tracking_only",
    },
]


def build_tracking_variables(ticker: str = TARGET_REVIEW_TICKER) -> dict[str, Any]:
    return {
        "generated_at": now_ts(),
        "ticker": normalize_ticker(ticker),
        "tracking_variables": [dict(row) for row in TRACKING_VARIABLE_ROWS],
        "safety": {
            "tracking_variable_is_trading_signal": False,
            "supplier_share_confirmed": False,
            "official_consensus_confirmed": False,
            "customer_allocation_confirmed": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
        },
    }
