#!/usr/bin/env python3
"""Phase 39 contribution analysis for Phase 38 persisted evidence."""

from __future__ import annotations

import sqlite3
from collections import Counter
from typing import Any

from smr_semantic_evidence_persistence import ensure_semantic_evidence_candidate_table
from smr_targeted_candidate_inventory import TARGET_TICKER
from smr_targeted_candidate_quality_review import build_targeted_candidate_quality_review
from smr_wiki import now_ts


VARIABLE_TYPE_MAP = {
    "product_mix": "product_mix",
    "ASP_price_signal": "ASP_price_proxy",
    "order_visibility_signal": "order_visibility",
    "shipment_signal": "shipment",
    "customer_allocation_signal": "customer_allocation_proxy",
}


def _review_variable_index(conn: sqlite3.Connection, ticker: str) -> dict[str, str]:
    review = build_targeted_candidate_quality_review(conn, ticker)
    rows = (review.get("candidate_quality_review") or {}).get("quality_rows") or []
    return {str(row.get("candidate_id")): str(row.get("variable") or "") for row in rows if row.get("candidate_id")}


def _phase38_candidate_ids(conn: sqlite3.Connection, ticker: str) -> list[str]:
    return list(_review_variable_index(conn, ticker))


def _canonical_variable(evidence_id: str, variable_type: str, review_index: dict[str, str]) -> str:
    return review_index.get(str(evidence_id)) or VARIABLE_TYPE_MAP.get(str(variable_type), str(variable_type or "unknown"))


def load_phase38_persisted_evidence(conn: sqlite3.Connection, ticker: str = TARGET_TICKER) -> list[dict[str, Any]]:
    """Return persisted Phase 38 evidence rows that still match Phase 37 dry-run candidates."""

    ticker = str(ticker or TARGET_TICKER).strip().upper()
    ensure_semantic_evidence_candidate_table(conn)
    review_index = _review_variable_index(conn, ticker)
    ids = _phase38_candidate_ids(conn, ticker)
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"""
        SELECT evidence_id, ticker, source_id, source_url, source_type, chunk_id,
               quoted_span, variable_type, claim_text, evidence_status, allowed_usage,
               usable_for_expectation_gap, usable_for_valuation_support, usable_for_promotion,
               limitations_json, payload_json, created_at, updated_at
        FROM semantic_evidence_candidates
        WHERE ticker=? AND evidence_id IN ({placeholders})
        ORDER BY evidence_id
        """,
        (ticker, *ids),
    ).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        evidence_id = str(row[0])
        variable_type = str(row[7] or "")
        result.append(
            {
                "evidence_id": evidence_id,
                "ticker": row[1],
                "source_id": row[2],
                "source_url": row[3],
                "source_type": row[4],
                "chunk_id": row[5],
                "quoted_span": row[6],
                "variable_type": variable_type,
                "variable": _canonical_variable(evidence_id, variable_type, review_index),
                "claim_text": row[8],
                "evidence_status": row[9],
                "allowed_usage": row[10],
                "usable_for_expectation_gap": bool(row[11]),
                "usable_for_valuation_support": bool(row[12]),
                "usable_for_promotion": bool(row[13]),
                "created_at": row[16],
                "updated_at": row[17],
            }
        )
    return result


def _support_boundary(variable: str) -> tuple[str, list[str], list[str]]:
    if variable == "product_mix":
        return (
            "supports_product_mix_upgrade",
            ["higher-end product exposure", "AI optical demand relevance", "margin or product mix context"],
            ["exact ASP", "confirmed supplier share", "confirmed customer allocation"],
        )
    if variable == "order_visibility":
        return (
            "supports_order_visibility",
            ["order visibility commentary", "demand visibility context", "bear case partial mitigation"],
            ["confirmed order", "named customer allocation", "contracted backlog number"],
        )
    if variable == "shipment":
        return (
            "supports_shipment_direction",
            ["shipment or delivery direction", "800G/1.6T demand relevance", "operating momentum context"],
            ["confirmed shipment number", "confirmed order", "confirmed supplier share"],
        )
    return (
        "supporting_context_only",
        ["contextual research support"],
        ["investment promotion", "confirmed sensitive variable"],
    )


def _preview(text: str, limit: int = 180) -> str:
    compact = " ".join(str(text or "").split())
    return compact if len(compact) <= limit else compact[: limit - 3].rstrip() + "..."


def build_evidence_contribution(conn: sqlite3.Connection, ticker: str = TARGET_TICKER) -> dict[str, Any]:
    ticker = str(ticker or TARGET_TICKER).strip().upper()
    evidence_rows = load_phase38_persisted_evidence(conn, ticker)
    contributions: list[dict[str, Any]] = []
    for row in evidence_rows:
        variable = str(row.get("variable") or "unknown")
        contribution_type, supports, does_not_support = _support_boundary(variable)
        contributions.append(
            {
                "evidence_id": row.get("evidence_id"),
                "variable": variable,
                "source_type": row.get("source_type"),
                "source_url": row.get("source_url"),
                "contribution_type": contribution_type,
                "strength": "supporting",
                "quoted_span_preview": _preview(str(row.get("quoted_span") or "")),
                "what_it_supports": supports,
                "what_it_does_not_support": does_not_support,
                "allowed_usage": row.get("allowed_usage"),
            }
        )
    variables = sorted(Counter(row.get("variable") for row in contributions))
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "evidence_contribution": {
            "new_evidence_count": len(contributions),
            "variables_strengthened": variables,
            "contribution_rows": contributions,
            "summary_judgment": (
                "New evidence modestly strengthens product mix, order visibility and shipment support, "
                "but does not close supplier share / official consensus / confirmed customer allocation gaps."
                if contributions
                else "No persisted Phase 38 evidence is available yet, so contribution remains unchanged."
            ),
        },
        "safety": {
            "product_mix_converted_to_confirmed_asp": False,
            "order_visibility_converted_to_confirmed_order": False,
            "shipment_commentary_converted_to_number": False,
            "customer_allocation_confirmed": False,
            "investment_advice_generated": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }
