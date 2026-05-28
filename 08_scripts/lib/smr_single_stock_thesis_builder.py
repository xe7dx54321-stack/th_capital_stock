#!/usr/bin/env python3
"""Phase 35 single-stock thesis synthesis.

This module is read-only. It synthesizes the Phase 34 research state into a
plain research thesis without creating pending reviews, paper orders, or trade
instructions.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_evidence_review_workbench import COMPANY_NAMES
from smr_post_governance_evidence_state import CORE_GAP_VARIABLES, build_post_governance_evidence_state
from smr_research_state_classifier import build_research_state_classification
from smr_supplier_exposure_model import get_supplier_exposure_profile
from smr_wiki import now_ts


PHASE35_PACKET_TICKERS = ["300394.SZ", "300308.SZ"]
DEFAULT_THEME = "ai_optical_interconnect"


def _first_row(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("ticker_results") or []
    return dict(rows[0]) if rows else {}


def _company_name(ticker: str, profile: dict[str, Any], evidence_row: dict[str, Any]) -> str | None:
    return profile.get("company_name") or evidence_row.get("company_name") or COMPANY_NAMES.get(ticker)


def _readable_gap(variable: str) -> str:
    mapping = {
        "supplier_share": "supplier share unconfirmed",
        "ASP_price_proxy": "ASP trend missing",
        "customer_allocation_proxy": "customer allocation missing",
        "official_consensus": "official consensus missing",
    }
    return mapping.get(variable, f"{variable} missing")


def _positive_drivers(profile: dict[str, Any], evidence_row: dict[str, Any], state_row: dict[str, Any]) -> list[str]:
    drivers: list[str] = []
    theme = profile.get("theme") or DEFAULT_THEME
    if theme == DEFAULT_THEME:
        drivers.append("AI optical demand remains a relevant research theme")
    if profile.get("product_exposure"):
        drivers.append("product exposure evidence remains supportive")
    snapshot = evidence_row.get("variable_pack_snapshot") or {}
    if snapshot.get("capacity") in {"partial", "proxy_supported", "confirmed"}:
        drivers.append("capacity-related evidence is partially supportive")
    for item in state_row.get("positive_factors") or []:
        if item and "no reviewed evidence" not in str(item):
            drivers.append(str(item))
    return list(dict.fromkeys(drivers)) or ["research theme remains plausible but needs more evidence"]


def _negative_drivers(evidence_row: dict[str, Any], state_row: dict[str, Any]) -> list[str]:
    gaps = evidence_row.get("remaining_core_gaps") or CORE_GAP_VARIABLES
    drivers = [_readable_gap(str(gap)) for gap in gaps]
    for item in state_row.get("negative_factors") or []:
        text = str(item)
        if text and "missing" not in text:
            drivers.append(text)
    return list(dict.fromkeys(drivers))


def build_single_stock_thesis(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    """Build a conservative research thesis for one ticker."""

    ticker = str(ticker or "").strip().upper()
    profile = get_supplier_exposure_profile(ticker)
    evidence_row = _first_row(build_post_governance_evidence_state(conn, tickers=ticker))
    state_row = _first_row(build_research_state_classification(conn, tickers=ticker))
    company = _company_name(ticker, profile, evidence_row)
    theme = profile.get("theme") or DEFAULT_THEME
    research_state = state_row.get("research_state") or "unchanged_needs_more_data"
    positives = _positive_drivers(profile, evidence_row, state_row)
    negatives = _negative_drivers(evidence_row, state_row)
    subject = company or ticker
    thesis_summary = (
        f"{subject} may benefit from AI optical interconnect demand expansion, "
        "but the benefit is not confirmed because supplier share, ASP, customer "
        "allocation, and official consensus evidence remain incomplete."
    )
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "company_name": company,
        "research_thesis": {
            "primary_theme": theme,
            "thesis_type": "supply_chain_expectation_gap",
            "thesis_summary": thesis_summary,
            "thesis_confidence": "medium_low",
            "positive_drivers": positives,
            "negative_drivers": negatives,
            "research_state": research_state,
            "promotion_boundary": {
                "promotion_allowed": False,
                "new_pending_created": False,
                "paper_order_created": False,
                "reason": "single-stock thesis synthesis only",
            },
        },
        "safety": {
            "is_investment_recommendation": False,
            "valuation_number_generated": False,
            "position_sizing_generated": False,
            "promotion_rules_relaxed": False,
        },
    }
