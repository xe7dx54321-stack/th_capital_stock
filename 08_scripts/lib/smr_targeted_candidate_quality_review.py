#!/usr/bin/env python3
"""Phase 38 quality review for targeted Phase 37 evidence candidates."""

from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict
from typing import Any

from smr_semantic_evidence_quality import score_semantic_candidate
from smr_targeted_candidate_inventory import (
    TARGET_TICKER,
    canonical_candidate_variable,
    candidate_warning_flags,
    has_explicit_asp_language,
    load_phase37_targeted_candidate_rows,
)
from smr_wiki import now_ts


SENSITIVE_VARIABLES = {"customer_allocation_proxy", "supplier_share", "official_consensus"}
PERSISTABLE_BUCKETS = {"usable", "weak_but_usable", "high_quality"}


def _duplicate_counts(candidates: list[dict[str, Any]]) -> Counter[tuple[str, str]]:
    return Counter(
        (
            str(candidate.get("source_url") or ""),
            " ".join(str(candidate.get("quoted_span") or "").split()),
        )
        for candidate in candidates
    )


def _allowed_usage_after_review(candidate: dict[str, Any], variable: str) -> str:
    if variable == "customer_allocation_proxy":
        return "scenario_analysis_only"
    if variable == "product_mix":
        return "valuation_support" if "margin" in str(candidate.get("quoted_span") or "").lower() or "毛利率" in str(candidate.get("quoted_span") or "") else "supporting_evidence"
    if variable == "ASP_price_proxy":
        return "valuation_support" if has_explicit_asp_language(candidate) else "supporting_evidence"
    if variable in {"shipment", "order_visibility"}:
        return "supporting_evidence"
    return str(candidate.get("allowed_usage") or "context_only")


def _review_reasons(candidate: dict[str, Any], variable: str, duplicate_count: int) -> list[str]:
    reasons = candidate_warning_flags(candidate)
    if duplicate_count > 1:
        reasons.append("duplicate_quoted_span_risk")
    if variable in SENSITIVE_VARIABLES:
        reasons.append("sensitive_variable")
    if variable == "customer_allocation_proxy":
        reasons.append("not_confirmed_allocation")
    if str(candidate.get("variable_type") or "") == "ASP_price_signal" and not has_explicit_asp_language(candidate):
        reasons.append("no_explicit_asp_or_price")
    return list(dict.fromkeys(reasons))


def _recommended_action(variable: str, quality_bucket: str, reasons: list[str]) -> str:
    if "missing_source_url" in reasons or "missing_quoted_span" in reasons or "quoted_span_not_in_claim_text" in reasons:
        return "reject"
    if quality_bucket == "reject":
        return "reject"
    if variable == "customer_allocation_proxy":
        return "downgrade_usage"
    if quality_bucket == "review_required":
        return "review_required"
    if quality_bucket in PERSISTABLE_BUCKETS:
        return "persist_candidate"
    return "review_required"


def calibrate_candidate_for_persistence(candidate: dict[str, Any], variable: str, allowed_usage: str) -> dict[str, Any]:
    updated = dict(candidate)
    if variable == "product_mix":
        updated["variable_type"] = "product_mix"
    elif variable == "ASP_price_proxy":
        updated["variable_type"] = "ASP_price_signal"
    elif variable == "shipment":
        updated["variable_type"] = "shipment_signal"
    elif variable == "order_visibility":
        updated["variable_type"] = "order_visibility_signal"
    elif variable == "customer_allocation_proxy":
        updated["variable_type"] = "customer_allocation_signal"
    updated["allowed_usage"] = allowed_usage
    updated["usable_for_expectation_gap"] = variable in {"shipment", "order_visibility"}
    updated["usable_for_valuation_support"] = variable in {"ASP_price_proxy", "product_mix"}
    updated["usable_for_promotion"] = False
    if variable == "customer_allocation_proxy":
        updated["evidence_status"] = "context_only"
        updated["usable_for_valuation_support"] = False
    payload = dict(updated.get("payload") or {})
    payload["phase38_calibration"] = {
        "variable_after_review": variable,
        "allowed_usage_after_review": allowed_usage,
        "usable_for_promotion": False,
        "confirmed_sensitive_variable": False,
    }
    updated["payload"] = payload
    return updated


def build_targeted_candidate_quality_review(conn: sqlite3.Connection, ticker: str = TARGET_TICKER) -> dict[str, Any]:
    ticker = str(ticker or TARGET_TICKER).strip().upper()
    candidates = load_phase37_targeted_candidate_rows(conn, ticker)
    duplicates = _duplicate_counts(candidates)
    rows: list[dict[str, Any]] = []
    counters: Counter[str] = Counter()
    duplicate_seen: defaultdict[tuple[str, str], int] = defaultdict(int)
    for candidate in candidates:
        variable = canonical_candidate_variable(candidate)
        duplicate_key = (str(candidate.get("source_url") or ""), " ".join(str(candidate.get("quoted_span") or "").split()))
        duplicate_seen[duplicate_key] += 1
        quality = score_semantic_candidate(candidate)
        bucket = str(quality.get("quality_bucket") or "reject")
        if variable == "customer_allocation_proxy" and bucket in {"high_quality", "usable"}:
            bucket = "review_required"
        if bucket == "high_quality":
            bucket = "usable"
        reasons = _review_reasons(candidate, variable, duplicates.get(duplicate_key, 0))
        allowed_usage = _allowed_usage_after_review(candidate, variable)
        action = _recommended_action(variable, bucket, reasons)
        eligible = action == "persist_candidate"
        calibrated = calibrate_candidate_for_persistence(candidate, variable, allowed_usage)
        quality_score = min(int(quality.get("quality_score") or 0), 84)
        if bucket == "review_required":
            quality_score = min(quality_score, 69)
        row = {
            "candidate_id": candidate.get("evidence_id"),
            "task_id": (candidate.get("payload") or {}).get("task_id"),
            "variable": variable,
            "raw_variable_type": candidate.get("variable_type"),
            "quality_score": quality_score,
            "quality_bucket": bucket,
            "quality_dimensions": quality.get("quality_dimensions") or {},
            "noise_flags": (quality.get("noise") or {}).get("noise_types") or [],
            "sensitive_flags": [variable] if variable in SENSITIVE_VARIABLES else [],
            "duplication_risk": duplicates.get(duplicate_key, 0) > 1,
            "duplicate_group_size": duplicates.get(duplicate_key, 0),
            "recommended_action": action,
            "allowed_usage_after_review": allowed_usage,
            "usable_for_promotion": False,
            "eligible_for_persistence": eligible,
            "review_reasons": reasons,
            "limitations": list(dict.fromkeys([*(candidate.get("limitations") or []), *quality.get("limitations", [])])),
            "source_url": candidate.get("source_url"),
            "quoted_span": candidate.get("quoted_span"),
            "calibrated_candidate": calibrated if eligible else None,
        }
        rows.append(row)
        counters[bucket] += 1
    eligible_rows = [row for row in rows if row.get("eligible_for_persistence")]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "candidate_quality_review": {
            "candidates_reviewed": len(rows),
            "high_quality": counters.get("high_quality", 0),
            "usable": counters.get("usable", 0),
            "weak_but_usable": counters.get("weak_but_usable", 0),
            "review_required": counters.get("review_required", 0),
            "reject": counters.get("reject", 0),
            "eligible_for_persistence": len(eligible_rows),
            "blocked_by_sensitive_guard": sum(1 for row in rows if row.get("sensitive_flags") and not row.get("eligible_for_persistence")),
            "usable_for_promotion_true": 0,
            "quality_rows": rows,
        },
        "safety": {
            "product_mix_auto_converted_to_asp": False,
            "customer_allocation_confirmed": False,
            "semantic_evidence_direct_promotion": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def eligible_calibrated_candidates(review_payload: dict[str, Any], *, limit: int | None = None) -> list[dict[str, Any]]:
    rows = (review_payload.get("candidate_quality_review") or {}).get("quality_rows") or []
    eligible_rows = [row for row in rows if row.get("eligible_for_persistence") and row.get("calibrated_candidate")]
    selected_rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for variable in ("ASP_price_proxy", "product_mix", "order_visibility", "shipment", "industry_forecast"):
        for row in eligible_rows:
            candidate_id = str(row.get("candidate_id") or "")
            if row.get("variable") == variable and candidate_id not in seen_ids:
                selected_rows.append(row)
                seen_ids.add(candidate_id)
                break
    for row in eligible_rows:
        candidate_id = str(row.get("candidate_id") or "")
        if candidate_id in seen_ids:
            continue
        selected_rows.append(row)
        seen_ids.add(candidate_id)
    candidates = [row.get("calibrated_candidate") for row in selected_rows]
    if limit is not None:
        candidates = candidates[: max(0, int(limit))]
    return candidates
