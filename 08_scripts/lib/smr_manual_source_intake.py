#!/usr/bin/env python3
"""Manual source intake templates for Phase 42."""

from __future__ import annotations

from typing import Any

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


INTAKE_SOURCE_TYPES = {
    "authorized_consensus_source",
    "company_direct_disclosure",
    "customer_side_public_statement",
    "industry_forecast_source",
    "sell_side_authorized_note",
    "manual_channel_check_note",
    "scenario_assumption",
    "proxy_evidence_note",
}

TEMPLATE_BY_EVIDENCE_TYPE: dict[str, dict[str, Any]] = {
    "official_consensus": {
        "source_type": "authorized_consensus_source",
        "allowed_usage_requested": "expectation_gap_benchmark",
        "limitations": [
            "requires authorized_or_user_provided permission",
            "internal proxy cannot fulfill official consensus",
        ],
    },
    "supplier_share": {
        "source_type": "scenario_assumption",
        "allowed_usage_requested": "scenario_analysis_only",
        "limitations": [
            "scenario assumption is not confirmed supplier share",
            "direct disclosure required for any confirmed usage",
        ],
    },
    "confirmed_customer_allocation": {
        "source_type": "proxy_evidence_note",
        "allowed_usage_requested": "bear_case_context_or_scenario_support",
        "limitations": [
            "proxy evidence cannot confirm allocation",
            "company or customer-side direct statement required for confirmed usage",
        ],
    },
}


def build_manual_source_intake_template(
    ticker: str = TARGET_REVIEW_TICKER,
    evidence_type: str = "official_consensus",
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    template = TEMPLATE_BY_EVIDENCE_TYPE.get(evidence_type)
    if not template:
        raise ValueError(f"Unsupported manual intake evidence type: {evidence_type}")
    body = {
        "source_type": template["source_type"],
        "source_title": "",
        "source_provider": "",
        "source_date": "",
        "source_url_or_reference": "",
        "permission_status": "authorized_or_user_provided",
        "quoted_span": "",
        "evidence_type": evidence_type,
        "allowed_usage_requested": template["allowed_usage_requested"],
        "limitations": list(template["limitations"]),
        "user_notes": "",
    }
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "manual_source_intake_template": body,
        "safety": {
            "template_only": True,
            "evidence_written": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }
