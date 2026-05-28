#!/usr/bin/env python3
"""Audit customer-allocation proxy evidence boundaries for Phase 42."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_evidence_lifecycle import list_semantic_evidence_candidates
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


CUSTOMER_ALLOCATION_VARIABLES = {"customer_allocation_signal", "customer_allocation_proxy"}


def _proxy_rows(conn: sqlite3.Connection, ticker: str) -> list[dict[str, Any]]:
    rows = []
    try:
        candidates = list_semantic_evidence_candidates(conn, ticker=ticker)
    except sqlite3.OperationalError:
        candidates = []
    for candidate in candidates:
        variable = str(candidate.get("variable_type") or "")
        if variable not in CUSTOMER_ALLOCATION_VARIABLES:
            continue
        rows.append(
            {
                "evidence_id": candidate.get("evidence_id"),
                "claim_type": "customer_allocation_proxy",
                "status": "proxy_only",
                "allowed_usage": "bear_case_context_or_scenario_support",
                "why_not_confirmed": [
                    "no direct customer statement",
                    "no company direct disclosure",
                    "generic customer reference only",
                ],
                "quoted_span_preview": str(candidate.get("quoted_span") or "")[:180],
            }
        )
    if not rows:
        for reference in (
            "generic_customer_reference_boundary",
            "north_america_customer_reference_boundary",
            "order_visibility_boundary",
        ):
            rows.append(
                {
                    "evidence_id": None,
                    "audit_reference": reference,
                    "claim_type": "customer_allocation_proxy",
                    "status": "proxy_only",
                    "allowed_usage": "bear_case_context_or_scenario_support",
                    "why_not_confirmed": [
                        "no direct customer statement",
                        "no company direct disclosure",
                        "boundary check only; no evidence row fabricated",
                    ],
                    "quoted_span_preview": "",
                }
            )
    return rows


def build_customer_allocation_proxy_audit(
    conn: sqlite3.Connection,
    ticker: str = TARGET_REVIEW_TICKER,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    rows = _proxy_rows(conn, ticker)
    confirmed = [
        row for row in rows
        if row.get("status") == "confirmed" or row.get("allowed_usage") == "confirmed_customer_allocation"
    ]
    violations = [
        row for row in rows
        if row.get("status") != "proxy_only" or "confirmed" in str(row.get("allowed_usage") or "")
    ]
    body = {
        "proxy_items_checked": len(rows),
        "confirmed_allocation_items": len(confirmed),
        "proxy_only_items": len(rows) - len(confirmed),
        "violations": len(violations),
        "audit_rows": rows,
        "do_not_do": [
            "do not treat customer proxy as confirmed allocation",
            "do not infer NVIDIA allocation from North America customer references",
            "do not treat order visibility as confirmed allocation",
        ],
    }
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "customer_allocation_proxy_audit": body,
        "safety": {
            "customer_allocation_confirmed": False,
            "evidence_written": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }
