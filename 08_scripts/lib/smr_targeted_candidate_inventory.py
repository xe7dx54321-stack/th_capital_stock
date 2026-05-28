#!/usr/bin/env python3
"""Phase 38 inventory helpers for targeted Phase 37 evidence candidates."""

from __future__ import annotations

import sqlite3
from collections import Counter
from typing import Any

from smr_targeted_evidence_candidate_builder import build_targeted_evidence_candidates
from smr_wiki import now_ts


TARGET_TICKER = "300308.SZ"


RAW_VARIABLE_MAP = {
    "ASP_price_signal": "ASP_price_proxy",
    "shipment_signal": "shipment",
    "order_visibility_signal": "order_visibility",
    "customer_allocation_signal": "customer_allocation_proxy",
    "industry_forecast": "industry_forecast",
    "product_mix": "product_mix",
}

PRODUCT_MIX_TERMS = (
    "product mix",
    "product structure",
    "mix",
    "margin",
    "gross margin",
    "800g",
    "1.6t",
    "silicon photonics",
    "硅光",
    "产品结构",
    "毛利率",
    "高端产品",
    "良率",
)

EXPLICIT_ASP_TERMS = ("asp", "price", "pricing", "单价", "价格", "售价")


def load_phase37_targeted_candidate_rows(conn: sqlite3.Connection, ticker: str = TARGET_TICKER) -> list[dict[str, Any]]:
    """Return Phase 37 dry-run candidate rows without writing state."""

    payload = build_targeted_evidence_candidates(conn, ticker, mode="dry_run")
    body = payload.get("targeted_evidence_candidates") or {}
    rows = [*(body.get("candidate_rows") or []), *(body.get("rejected_rows") or [])]
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        evidence_id = str(row.get("evidence_id") or "")
        if not evidence_id or evidence_id in seen:
            continue
        seen.add(evidence_id)
        deduped.append(row)
    return deduped


def has_explicit_asp_language(candidate: dict[str, Any]) -> bool:
    text = str(candidate.get("quoted_span") or candidate.get("claim_text") or "").lower()
    return any(term.lower() in text for term in EXPLICIT_ASP_TERMS)


def has_product_mix_language(candidate: dict[str, Any]) -> bool:
    text = str(candidate.get("quoted_span") or candidate.get("claim_text") or "").lower()
    return any(term.lower() in text for term in PRODUCT_MIX_TERMS)


def canonical_candidate_variable(candidate: dict[str, Any]) -> str:
    raw = str(candidate.get("variable_type") or "")
    if raw == "ASP_price_signal" and not has_explicit_asp_language(candidate) and has_product_mix_language(candidate):
        return "product_mix"
    return RAW_VARIABLE_MAP.get(raw, raw or "unknown")


def candidate_warning_flags(candidate: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    quoted = str(candidate.get("quoted_span") or "")
    claim = str(candidate.get("claim_text") or "")
    if not candidate.get("source_url"):
        warnings.append("missing_source_url")
    if not quoted:
        warnings.append("missing_quoted_span")
    if quoted and claim and quoted not in claim:
        warnings.append("quoted_span_not_in_claim_text")
    if candidate.get("variable_type") == "ASP_price_signal" and not has_explicit_asp_language(candidate):
        warnings.append("asp_not_explicit_product_or_margin_proxy_only")
    if candidate.get("variable_type") == "customer_allocation_signal":
        warnings.append("customer_allocation_proxy_not_confirmed")
    return warnings


def inventory_row(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = candidate.get("payload") or {}
    return {
        "candidate_id": candidate.get("evidence_id"),
        "task_id": payload.get("task_id"),
        "variable": canonical_candidate_variable(candidate),
        "raw_variable_type": candidate.get("variable_type"),
        "source_id": candidate.get("source_id"),
        "source_type": candidate.get("source_type"),
        "source_url": candidate.get("source_url"),
        "quoted_span": candidate.get("quoted_span"),
        "allowed_usage_suggestion": candidate.get("allowed_usage"),
        "limitations": candidate.get("limitations") or [],
        "warnings": candidate_warning_flags(candidate),
    }


def build_targeted_candidate_inventory(conn: sqlite3.Connection, ticker: str = TARGET_TICKER) -> dict[str, Any]:
    ticker = str(ticker or TARGET_TICKER).strip().upper()
    candidates = load_phase37_targeted_candidate_rows(conn, ticker)
    rows = [inventory_row(candidate) for candidate in candidates]
    by_variable = Counter(str(row.get("variable") or "unknown") for row in rows)
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "candidate_inventory": {
            "candidates_total": len(rows),
            "by_variable": dict(sorted(by_variable.items())),
            "candidates": rows,
            "skip_reason": None if rows else "no_phase37_dry_run_candidates_available",
        },
        "safety": {
            "inventory_only": True,
            "evidence_written": False,
            "investment_advice_generated": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }
