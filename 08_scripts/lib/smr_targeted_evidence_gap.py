#!/usr/bin/env python3
"""Phase 36 targeted evidence-gap analysis.

The functions here are planning-only. They read existing research packet and
evidence state, then describe what evidence is still needed without fetching
sources, writing evidence, creating pending reviews, or relaxing promotion.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_evidence_review_workbench import COMPANY_NAMES
from smr_research_evidence_chain import build_research_evidence_chain
from smr_research_quality_scoring import build_research_quality_score, build_variable_coverage_matrix
from smr_supplier_exposure_model import get_supplier_exposure_profile
from smr_wiki import now_ts


FOCUS_VARIABLES = [
    "supplier_share",
    "ASP_price_proxy",
    "customer_allocation_proxy",
    "official_consensus",
    "shipment",
    "order_visibility",
    "industry_forecast",
    "margin_signal",
    "product_exposure",
]

GAP_DEFINITIONS: dict[str, dict[str, Any]] = {
    "supplier_share": {
        "evidence_need": "company-specific supplier exposure or tightly caveated share range",
        "target_evidence_type": "supplier share disclosure or scenario assumption support",
        "why_it_matters": "supplier share is needed to translate AI optical demand into company-specific revenue sensitivity",
        "can_be_confirmed_from_public_sources": False,
        "allowed_usage_if_found": "scenario_analysis_only_or_supporting_evidence",
        "criticality": "critical",
    },
    "ASP_price_proxy": {
        "evidence_need": "product mix, ASP direction, pricing commentary, or margin impact evidence",
        "target_evidence_type": "company commentary or industry pricing trend",
        "why_it_matters": "ASP or price direction is needed to assess revenue and margin sensitivity",
        "can_be_confirmed_from_public_sources": "partial_only",
        "allowed_usage_if_found": "valuation_support",
        "criticality": "critical",
    },
    "customer_allocation_proxy": {
        "evidence_need": "public customer-side signal or company caveated customer exposure commentary",
        "target_evidence_type": "customer allocation proxy, not confirmed allocation",
        "why_it_matters": "customer allocation uncertainty is a major bear-case driver",
        "can_be_confirmed_from_public_sources": False,
        "allowed_usage_if_found": "scenario_analysis_only",
        "criticality": "critical",
    },
    "official_consensus": {
        "evidence_need": "authorized official consensus source",
        "target_evidence_type": "commercial or authorized consensus data",
        "why_it_matters": "official consensus is needed before expectation-gap confidence can be upgraded",
        "can_be_confirmed_from_public_sources": False,
        "allowed_usage_if_found": "valuation_support",
        "criticality": "critical",
    },
    "shipment": {
        "evidence_need": "shipment trend, delivery, or order conversion evidence",
        "target_evidence_type": "IR or filing commentary on shipments and delivery cadence",
        "why_it_matters": "shipment visibility connects demand commentary to actual delivery progress",
        "can_be_confirmed_from_public_sources": "partial_only",
        "allowed_usage_if_found": "supporting_evidence",
        "criticality": "critical",
    },
    "order_visibility": {
        "evidence_need": "order cadence, backlog, or customer demand visibility evidence",
        "target_evidence_type": "IR discussion of orders without assuming confirmed customer allocation",
        "why_it_matters": "order visibility helps test whether demand evidence is near-term and company-specific",
        "can_be_confirmed_from_public_sources": "partial_only",
        "allowed_usage_if_found": "supporting_evidence",
        "criticality": "critical",
    },
    "industry_forecast": {
        "evidence_need": "public industry forecast for 800G/1.6T demand, pricing, or AI optical buildout",
        "target_evidence_type": "industry public forecast",
        "why_it_matters": "industry forecast provides external context but cannot replace company-specific evidence",
        "can_be_confirmed_from_public_sources": "partial_only",
        "allowed_usage_if_found": "context_or_valuation_support",
        "criticality": "critical",
    },
    "margin_signal": {
        "evidence_need": "margin or product-mix evidence tied to high-speed optical products",
        "target_evidence_type": "company margin/product mix commentary",
        "why_it_matters": "margin and product mix evidence helps test whether demand converts into earnings sensitivity",
        "can_be_confirmed_from_public_sources": "partial_only",
        "allowed_usage_if_found": "supporting_evidence",
        "criticality": "important",
    },
    "product_exposure": {
        "evidence_need": "continued product exposure evidence for high-speed optical modules",
        "target_evidence_type": "company product exposure commentary",
        "why_it_matters": "product exposure keeps the thesis anchored to the relevant AI optical chain",
        "can_be_confirmed_from_public_sources": "partial_only",
        "allowed_usage_if_found": "supporting_evidence",
        "criticality": "important",
    },
}


def _company_name(ticker: str) -> str | None:
    profile = get_supplier_exposure_profile(ticker)
    return profile.get("company_name") or COMPANY_NAMES.get(ticker)


def _matrix_by_variable(conn: sqlite3.Connection, ticker: str) -> dict[str, dict[str, Any]]:
    payload = build_variable_coverage_matrix(conn, ticker)
    return {str(row.get("variable")): row for row in payload.get("variable_matrix") or []}


def _quality(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    return build_research_quality_score(conn, ticker).get("research_quality") or {}


def _supported_variables(matrix: dict[str, dict[str, Any]]) -> list[str]:
    supported = []
    for variable, row in matrix.items():
        if int(row.get("evidence_count") or 0) > 0 and row.get("status") in {"partial", "context_only", "supporting_evidence"}:
            supported.append(variable)
    return sorted(supported)


def _gap_row(variable: str, matrix_row: dict[str, Any]) -> dict[str, Any]:
    definition = GAP_DEFINITIONS[variable]
    status = str(matrix_row.get("status") or "missing")
    evidence_count = int(matrix_row.get("evidence_count") or 0)
    confirmed = bool(matrix_row.get("confirmed"))
    if variable in {"supplier_share", "customer_allocation_proxy", "official_consensus"}:
        confirmed = False
    gap_status = "missing" if status == "missing" or evidence_count == 0 else "insufficient_direct_evidence"
    return {
        "variable": variable,
        "evidence_need": definition["evidence_need"],
        "current_status": status,
        "current_evidence_count": evidence_count,
        "target_evidence_type": definition["target_evidence_type"],
        "impact_on_thesis": matrix_row.get("impact_on_thesis") or "medium",
        "criticality": definition["criticality"],
        "gap_status": gap_status,
        "why_it_matters": definition["why_it_matters"],
        "can_be_confirmed_from_public_sources": definition["can_be_confirmed_from_public_sources"],
        "allowed_usage_if_found": definition["allowed_usage_if_found"],
        "confirmed_after_plan": confirmed,
    }


def build_targeted_evidence_gap(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    ticker = str(ticker or "").strip().upper()
    matrix = _matrix_by_variable(conn, ticker)
    quality = _quality(conn, ticker)
    evidence_chain = build_research_evidence_chain(conn, ticker).get("evidence_chain") or {}
    gap_rows = [_gap_row(variable, matrix.get(variable, {"variable": variable, "status": "missing"})) for variable in FOCUS_VARIABLES]
    critical = [row for row in gap_rows if row.get("criticality") == "critical"]
    non_critical = [row for row in gap_rows if row.get("criticality") != "critical" and row.get("gap_status") == "missing"]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "company_name": _company_name(ticker),
        "targeted_evidence_gap": {
            "research_quality_before": quality.get("overall_quality"),
            "evidence_coverage_before": quality.get("evidence_coverage"),
            "research_readiness": quality.get("research_readiness"),
            "semantic_evidence_total": evidence_chain.get("total_evidence"),
            "critical_missing_variables": critical,
            "non_critical_missing_variables": non_critical,
            "variables_already_supported": _supported_variables(matrix),
        },
        "safety": {
            "gap_analysis_only": True,
            "investment_advice_generated": False,
            "confirmed_sensitive_variable_fabricated": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }
