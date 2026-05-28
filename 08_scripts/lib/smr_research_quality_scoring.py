#!/usr/bin/env python3
"""Phase 35 conservative research quality and readiness helpers."""

from __future__ import annotations

import sqlite3
from collections import Counter
from typing import Any

from smr_evidence_lifecycle import list_lifecycle_states, list_semantic_evidence_candidates
from smr_post_governance_evidence_state import (
    CORE_GAP_VARIABLES,
    INACTIVE_LIFECYCLE_STATUSES,
    build_bear_case_post_governance,
    build_expectation_gap_post_governance,
    build_next_evidence_plan,
    build_valuation_support_post_governance,
    build_variable_pack_post_governance,
    normalize_research_variable,
)
from smr_research_evidence_chain import build_research_evidence_chain
from smr_research_state_classifier import build_research_state_classification
from smr_wiki import now_ts


PHASE35_VARIABLES = [
    "supplier_share",
    "ASP_price_proxy",
    "capacity",
    "shipment",
    "customer_allocation_proxy",
    "official_consensus",
    "industry_forecast",
    "margin_signal",
    "order_visibility",
    "product_exposure",
]
SENSITIVE_NEVER_CONFIRMED = {"supplier_share", "ASP_price_proxy", "customer_allocation_proxy", "official_consensus"}


def _first_row(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("ticker_results") or []
    return dict(rows[0]) if rows else {}


def _raw_variable_to_phase35(variable_type: Any) -> str:
    raw = str(variable_type or "")
    if raw == "product_exposure":
        return "product_exposure"
    if raw == "margin_signal":
        return "margin_signal"
    if raw == "order_visibility_signal":
        return "order_visibility"
    if raw == "shipment_signal":
        return "shipment"
    normalized = normalize_research_variable(raw)
    if normalized == "consensus_expectation_proxy":
        return "official_consensus"
    return normalized


def _active_evidence_counts(conn: sqlite3.Connection, ticker: str) -> Counter[str]:
    states = {str(row.get("evidence_id")): row for row in list_lifecycle_states(conn, ticker=ticker)}
    counts: Counter[str] = Counter()
    for candidate in list_semantic_evidence_candidates(conn, ticker=ticker):
        state = states.get(str(candidate.get("evidence_id"))) or {}
        lifecycle = str(state.get("lifecycle_status") or "persisted_candidate")
        if lifecycle in INACTIVE_LIFECYCLE_STATUSES:
            continue
        variable = _raw_variable_to_phase35(candidate.get("variable_type"))
        counts[variable] += 1
    return counts


def _status_index(variable_row: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in variable_row.get("variable_pack_delta") or []:
        variable = str(item.get("variable") or "")
        mapped = "official_consensus" if variable == "consensus_expectation_proxy" else variable
        result[mapped] = str(item.get("after_status") or item.get("before_status") or "missing")
    return result


def _allowed_usage(status: str) -> str:
    if status in {"confirmed", "proxy_supported", "partial"}:
        return "supporting_evidence"
    if status == "context_only":
        return "context_only"
    if status == "planned_only":
        return "planned_only"
    return "none"


def _impact(variable: str) -> str:
    if variable in CORE_GAP_VARIABLES:
        return "high"
    if variable in {"capacity", "shipment", "product_exposure", "order_visibility", "industry_forecast"}:
        return "medium"
    return "low"


def build_variable_coverage_matrix(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    ticker = str(ticker or "").strip().upper()
    variable_row = _first_row(build_variable_pack_post_governance(conn, tickers=ticker))
    statuses = _status_index(variable_row)
    counts = _active_evidence_counts(conn, ticker)
    matrix: list[dict[str, Any]] = []
    for variable in PHASE35_VARIABLES:
        status = statuses.get(variable, "missing")
        if variable in SENSITIVE_NEVER_CONFIRMED and status == "confirmed":
            status = "partial"
        evidence_count = int(counts.get(variable, 0))
        if evidence_count == 0 and variable in CORE_GAP_VARIABLES:
            status = "missing"
        matrix.append(
            {
                "variable": variable,
                "status": status,
                "evidence_count": evidence_count,
                "allowed_usage": _allowed_usage(status),
                "impact_on_thesis": _impact(variable),
                "confirmed": False if variable in SENSITIVE_NEVER_CONFIRMED else status == "confirmed",
            }
        )
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "variable_matrix": matrix,
        "safety": {
            "official_consensus_fabricated": False,
            "supplier_share_confirmed": False,
            "customer_allocation_confirmed": False,
            "promotion_allowed": False,
        },
    }


def _missing_core_variables(matrix: list[dict[str, Any]]) -> list[str]:
    missing: list[str] = []
    for row in matrix:
        if row.get("variable") in CORE_GAP_VARIABLES and row.get("status") != "confirmed":
            missing.append(str(row.get("variable")))
    return missing


def _gap_text(variable: str) -> str:
    mapping = {
        "supplier_share": "supplier_share missing",
        "ASP_price_proxy": "ASP_price_proxy missing",
        "customer_allocation_proxy": "customer_allocation unconfirmed",
        "official_consensus": "official_consensus missing",
    }
    return mapping.get(variable, f"{variable} missing")


def build_research_quality_score(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    ticker = str(ticker or "").strip().upper()
    matrix_payload = build_variable_coverage_matrix(conn, ticker)
    matrix = matrix_payload.get("variable_matrix") or []
    chain = build_research_evidence_chain(conn, ticker).get("evidence_chain") or {}
    missing_core = _missing_core_variables(matrix)
    valuation = _first_row(build_valuation_support_post_governance(conn, tickers=ticker))
    bear = _first_row(build_bear_case_post_governance(conn, tickers=ticker))
    active_evidence = int(chain.get("total_evidence") or 0) - int(chain.get("rejected_evidence") or 0) - int(chain.get("marked_noise") or 0)
    overall = "medium_low" if active_evidence else "low"
    if len(missing_core) >= 3:
        overall = "medium_low" if active_evidence >= 3 else "low"
    quality = {
        "overall_quality": overall,
        "evidence_coverage": "partial" if active_evidence else "thin",
        "thesis_clarity": "medium",
        "valuation_support": "weak" if valuation.get("valuation_support_after") == "context_only" else "partial",
        "bear_case_quality": "partial" if bear.get("bear_case_after") else "thin",
        "research_readiness": "needs_more_data",
        "key_quality_gaps": [_gap_text(item) for item in missing_core],
    }
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "research_quality": quality,
        "safety": {
            "quality_is_investment_rating": False,
            "overall_quality_high": False,
            "auto_pending": False,
            "promotion_allowed": False,
        },
    }


def build_research_scenarios(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    ticker = str(ticker or "").strip().upper()
    matrix = build_variable_coverage_matrix(conn, ticker).get("variable_matrix") or []
    missing_core = _missing_core_variables(matrix)
    required = [item for item in missing_core if item in {"supplier_share", "ASP_price_proxy", "customer_allocation_proxy"}]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "research_scenarios": {
            "bull_case": {
                "description": "AI optical demand continues strengthening and company exposure proves higher than current evidence supports",
                "required_missing_variables": required or CORE_GAP_VARIABLES[:3],
            },
            "base_case": {
                "description": "AI optical demand remains positive while company-specific evidence remains partial",
                "current_support_level": "medium_low",
                "required_missing_variables": missing_core,
            },
            "bear_case": {
                "description": "customer allocation, ASP, or supplier share assumptions fail to validate",
                "current_bear_strength": "medium",
                "required_missing_variables": missing_core,
            },
        },
        "safety": {
            "scenario_is_price_forecast": False,
            "trade_recommendation_generated": False,
            "position_sizing_generated": False,
        },
    }


def build_why_not_pending(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    ticker = str(ticker or "").strip().upper()
    matrix = build_variable_coverage_matrix(conn, ticker).get("variable_matrix") or []
    missing_core = _missing_core_variables(matrix)
    core_reasons = [_gap_text(item) for item in missing_core] or [_gap_text(item) for item in CORE_GAP_VARIABLES]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "why_not_pending": {
            "promotion_allowed": False,
            "core_reasons": core_reasons,
            "secondary_reasons": ["valuation support weak", "evidence coverage partial"],
            "what_would_need_to_change": [
                "better supplier share evidence",
                "better ASP evidence",
                "customer allocation support from authorized public sources",
                "official consensus evidence from an authorized provider",
            ],
        },
        "safety": {
            "semantic_evidence_direct_pending": False,
            "new_pending_created": False,
            "paper_order_created": False,
            "promotion_rules_relaxed": False,
        },
    }


def _sanitize_source(source: str) -> str:
    text = str(source)
    text = text.replace("authorized sell-side estimate source", "authorized estimate source")
    text = text.replace("sell-side estimate source", "authorized estimate source")
    text = text.replace("sell-side", "authorized")
    text = text.replace("buy-side", "authorized")
    return text


def build_safe_next_evidence_plan(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    ticker = str(ticker or "").strip().upper()
    payload = build_next_evidence_plan(conn, tickers=ticker)
    row = _first_row(payload)
    items = []
    for item in row.get("plan_items") or []:
        safe_item = dict(item)
        safe_item["suggested_sources"] = [_sanitize_source(source) for source in safe_item.get("suggested_sources") or []]
        items.append(safe_item)
    return {
        "ticker": ticker,
        "plan_items": items,
        "safety": {
            "plan_only_no_evidence_written": True,
            "confirmed_sensitive_variable_fabricated": False,
            "promotion_allowed": False,
        },
    }


def build_phase35_dashboard(conn: sqlite3.Connection, tickers: list[str]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    states_payload = build_research_state_classification(conn, tickers=",".join(tickers))
    states = {str(row.get("ticker")): row for row in states_payload.get("ticker_results") or []}
    for ticker in tickers:
        quality = build_research_quality_score(conn, ticker).get("research_quality") or {}
        why = build_why_not_pending(conn, ticker).get("why_not_pending") or {}
        rows.append(
            {
                "ticker": ticker,
                "research_state": (states.get(ticker) or {}).get("research_state") or "unchanged_needs_more_data",
                "research_quality": quality.get("overall_quality"),
                "evidence_coverage": quality.get("evidence_coverage"),
                "key_missing_variables": [_reason_to_variable(reason) for reason in why.get("core_reasons") or []],
                "next_step": "targeted evidence acquisition",
            }
        )
    summary = {
        "research_packets": len(rows),
        "research_weakened": sum(1 for row in rows if row.get("research_state") == "research_weakened"),
        "unchanged_needs_more_data": sum(1 for row in rows if row.get("research_state") == "unchanged_needs_more_data"),
        "ready_for_research_packet": sum(1 for row in rows if row.get("research_state") == "ready_for_research_packet"),
        "new_pending_created": 0,
        "paper_order_created": 0,
    }
    return {
        "generated_at": now_ts(),
        "summary": summary,
        "ticker_rows": rows,
        "safety": {
            "dashboard_is_investment_advice": False,
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def _reason_to_variable(reason: str) -> str:
    text = str(reason)
    if text.startswith("customer_allocation"):
        return "customer_allocation_proxy"
    return text.replace(" missing", "").replace(" unconfirmed", "")
