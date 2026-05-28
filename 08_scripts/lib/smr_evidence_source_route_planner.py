#!/usr/bin/env python3
"""Phase 36 source-route planning for targeted evidence acquisition."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_targeted_evidence_gap import build_targeted_evidence_gap
from smr_wiki import now_ts


SOURCE_ROUTES: dict[str, list[dict[str, Any]]] = {
    "supplier_share": [
        {
            "route_type": "manual_research_required",
            "priority": "high",
            "expected_evidence_type": "range assumption with strict caveat",
            "allowed_usage": "scenario_analysis_only",
            "limitations": ["exact supplier share is usually not publicly disclosed"],
        },
        {
            "route_type": "not_publicly_confirmable",
            "priority": "high",
            "expected_evidence_type": "mark exact supplier share as unconfirmed unless direct disclosure exists",
            "allowed_usage": "none_for_confirmation",
            "limitations": ["do not fabricate confirmed share from semantic evidence"],
        },
    ],
    "ASP_price_proxy": [
        {
            "route_type": "company_ir",
            "priority": "high",
            "expected_evidence_type": "management commentary on product mix, ASP direction, price trend, or margin impact",
            "allowed_usage": "supporting_evidence",
            "limitations": ["may not disclose exact ASP"],
        },
        {
            "route_type": "industry_public_forecast",
            "priority": "medium",
            "expected_evidence_type": "800G/1.6T pricing or demand trend commentary",
            "allowed_usage": "context_or_valuation_support",
            "limitations": ["not company-specific"],
        },
    ],
    "customer_allocation_proxy": [
        {
            "route_type": "customer_side_public_signal",
            "priority": "high",
            "expected_evidence_type": "public customer-side demand or supplier qualification signal",
            "allowed_usage": "scenario_analysis_only",
            "limitations": ["does not confirm allocation share"],
        },
        {
            "route_type": "company_ir",
            "priority": "medium",
            "expected_evidence_type": "caveated customer exposure commentary",
            "allowed_usage": "supporting_evidence",
            "limitations": ["must not infer named customer allocation if undisclosed"],
        },
        {
            "route_type": "not_publicly_confirmable",
            "priority": "high",
            "expected_evidence_type": "mark exact customer allocation as unconfirmed without direct disclosure",
            "allowed_usage": "none_for_confirmation",
            "limitations": ["customer allocation is often confidential"],
        },
    ],
    "official_consensus": [
        {
            "route_type": "official_consensus_provider",
            "priority": "high",
            "expected_evidence_type": "authorized consensus estimate snapshot",
            "allowed_usage": "valuation_support",
            "limitations": ["requires authorized or commercial provider access"],
        },
        {
            "route_type": "authorized_sell_side_source",
            "priority": "medium",
            "expected_evidence_type": "authorized estimate source with clear provenance",
            "allowed_usage": "valuation_support",
            "limitations": ["internal proxy is not official consensus"],
        },
    ],
    "shipment": [
        {
            "route_type": "investor_relations_record",
            "priority": "high",
            "expected_evidence_type": "shipment or delivery cadence commentary",
            "allowed_usage": "supporting_evidence",
            "limitations": ["shipment commentary is not customer allocation"],
        }
    ],
    "order_visibility": [
        {
            "route_type": "company_ir",
            "priority": "high",
            "expected_evidence_type": "order visibility, backlog, demand cadence, or delivery constraint commentary",
            "allowed_usage": "supporting_evidence",
            "limitations": ["orders are not confirmed customer allocation unless explicitly disclosed"],
        }
    ],
    "industry_forecast": [
        {
            "route_type": "industry_public_forecast",
            "priority": "medium",
            "expected_evidence_type": "public AI optical demand, shipment, or pricing forecast",
            "allowed_usage": "context_or_valuation_support",
            "limitations": ["industry forecast cannot be treated as company-specific order evidence"],
        }
    ],
    "margin_signal": [
        {
            "route_type": "annual_report",
            "priority": "medium",
            "expected_evidence_type": "gross margin, product mix, or high-speed product profitability commentary",
            "allowed_usage": "supporting_evidence",
            "limitations": ["margin commentary does not reveal exact ASP"],
        },
        {
            "route_type": "investor_relations_record",
            "priority": "medium",
            "expected_evidence_type": "management commentary on product mix or margin impact",
            "allowed_usage": "supporting_evidence",
            "limitations": ["must preserve exact quoted span"],
        },
    ],
    "product_exposure": [
        {
            "route_type": "company_announcement",
            "priority": "medium",
            "expected_evidence_type": "company product exposure disclosure",
            "allowed_usage": "supporting_evidence",
            "limitations": ["product exposure is not supplier share"],
        }
    ],
}


def build_evidence_source_routes(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    gap = build_targeted_evidence_gap(conn, ticker)
    gap_body = gap.get("targeted_evidence_gap") or {}
    variables = [row.get("variable") for row in gap_body.get("critical_missing_variables") or []]
    routes = [{"variable": variable, "source_routes": SOURCE_ROUTES.get(str(variable), [])} for variable in variables]
    return {
        "generated_at": now_ts(),
        "ticker": gap.get("ticker"),
        "company_name": gap.get("company_name"),
        "source_routes": routes,
        "safety": {
            "route_planning_only": True,
            "supplier_share_public_confirmation_assumed": False,
            "customer_allocation_public_confirmation_assumed": False,
            "internal_proxy_treated_as_official_consensus": False,
            "evidence_written": False,
        },
    }
