#!/usr/bin/env python3
"""Quality scoring for semantic evidence candidates."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from smr_semantic_evidence_noise_filter import detect_noise


QUALITY_BUCKETS = {
    "high_quality",
    "usable",
    "weak_but_usable",
    "review_required",
    "reject",
}

PERSIST_BUCKETS = {"high_quality", "usable", "weak_but_usable"}


def quality_bucket(score: int) -> str:
    if score >= 85:
        return "high_quality"
    if score >= 70:
        return "usable"
    if score >= 50:
        return "weak_but_usable"
    if score >= 30:
        return "review_required"
    return "reject"


def _metadata(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = candidate.get("payload") or {}
    return payload.get("source_metadata") or {}


def _extraction(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = candidate.get("payload") or {}
    gate = payload.get("gate") or {}
    return gate.get("extraction") or {}


def _is_quantified(candidate: dict[str, Any]) -> bool:
    extraction = _extraction(candidate)
    if extraction.get("is_quantified"):
        return True
    return bool(re.search(r"\d", str(candidate.get("quoted_span") or "")))


def _is_direct(candidate: dict[str, Any]) -> bool:
    extraction = _extraction(candidate)
    strength = str(extraction.get("evidence_strength") or "").lower()
    return strength in {"direct_disclosure", "quantified_disclosure"}


def _is_management(candidate: dict[str, Any]) -> bool:
    extraction = _extraction(candidate)
    strength = str(extraction.get("evidence_strength") or "").lower()
    flags = [str(item).lower() for item in extraction.get("risk_flags") or []]
    return strength == "management_commentary" or "management_commentary" in flags


def _freshness_score(published_at: str | None) -> int:
    text = str(published_at or "")
    match = re.search(r"(20\d{2})", text)
    if not match:
        return 3
    year = int(match.group(1))
    if year >= 2026:
        return 8
    if year >= 2025:
        return 6
    return 3


def score_semantic_candidate(candidate: dict[str, Any], *, min_quality_score: int = 50, allow_review_required: bool = False) -> dict[str, Any]:
    quoted_span = str(candidate.get("quoted_span") or "")
    source_url = str(candidate.get("source_url") or "")
    variable_type = str(candidate.get("variable_type") or "unknown")
    metadata = _metadata(candidate)
    extraction = _extraction(candidate)
    noise = detect_noise(candidate)
    reasons: list[str] = []
    limitations = list(candidate.get("limitations") or extraction.get("limitations") or [])

    if not quoted_span:
        return _reject(candidate, noise, "missing quoted_span", limitations)
    if not source_url:
        return _reject(candidate, noise, "missing source_url", limitations)
    if variable_type == "unknown":
        return _reject(candidate, noise, "unknown variable_type", limitations)

    span_len = len(quoted_span.strip())
    dimensions = {
        "quoted_span_quality": 15 if span_len >= 28 else (7 if span_len >= 12 else 0),
        "source_quality": 12 if metadata.get("real_source") and source_url else (8 if source_url else 0),
        "section_quality": 10 if metadata.get("section_type") in {"qa_section", "capacity_expansion", "product_structure", "customer_market", "margin_price"} else 6,
        "variable_relevance": 14 if variable_type != "unknown" else 0,
        "specificity": 9 if extraction.get("is_company_specific", True) else 5,
        "quantification": 8 if _is_quantified(candidate) else 2,
        "freshness": _freshness_score(metadata.get("published_at")),
        "noise_risk": -min(15, int(round(float(noise.get("noise_score") or 0) * 18))),
        "duplication_risk": -2,
        "promotion_safety": 10 if not candidate.get("usable_for_promotion") else -20,
    }
    if _is_direct(candidate):
        dimensions["specificity"] += 4
        dimensions["quantification"] += 4
    if _is_management(candidate):
        dimensions["specificity"] = min(dimensions["specificity"], 8)
        reasons.append("management commentary capped at usable")
        if "management commentary" not in limitations:
            limitations.append("management commentary")
    if not _is_quantified(candidate) and "not quantified" not in limitations:
        limitations.append("not quantified")
    if metadata.get("section_type") == "qa_section":
        reasons.append("Q&A section preserved")
    if source_url:
        reasons.append("source_url present")
    if quoted_span:
        reasons.append("quoted_span present and traceable")
    if metadata.get("real_source"):
        reasons.append("company-specific real source metadata")
    if _is_quantified(candidate):
        reasons.append("contains original numeric values")
    if noise.get("noise_detected"):
        reasons.append(f"noise detected: {', '.join(noise.get('noise_types') or [])}")

    score = max(0, min(100, sum(dimensions.values())))
    bucket = quality_bucket(score)
    if _is_management(candidate) and bucket == "high_quality":
        bucket = "usable"
        score = min(score, 84)
    if noise.get("recommended_action") == "reject":
        bucket = "reject"
        score = min(score, 29)
    elif noise.get("recommended_action") == "review_required" and bucket not in {"reject", "review_required"}:
        bucket = "review_required"
        score = min(score, 49)

    recommendation = acceptance_recommendation(bucket, score, min_quality_score=min_quality_score, allow_review_required=allow_review_required)
    return {
        "evidence_id": candidate.get("evidence_id"),
        "ticker": candidate.get("ticker"),
        "source_id": candidate.get("source_id"),
        "chunk_id": candidate.get("chunk_id"),
        "variable_type": variable_type,
        "quality_score": int(score),
        "quality_bucket": bucket,
        "quality_dimensions": dimensions,
        "noise": noise,
        "acceptance_recommendation": recommendation,
        "reasons": reasons,
        "limitations": limitations,
    }


def _reject(candidate: dict[str, Any], noise: dict[str, Any], reason: str, limitations: list[str]) -> dict[str, Any]:
    return {
        "evidence_id": candidate.get("evidence_id"),
        "ticker": candidate.get("ticker"),
        "source_id": candidate.get("source_id"),
        "chunk_id": candidate.get("chunk_id"),
        "variable_type": candidate.get("variable_type") or "unknown",
        "quality_score": 0,
        "quality_bucket": "reject",
        "quality_dimensions": {
            "quoted_span_quality": 0,
            "source_quality": 0,
            "section_quality": 0,
            "variable_relevance": 0,
            "specificity": 0,
            "quantification": 0,
            "freshness": 0,
            "noise_risk": -20 if noise.get("noise_detected") else 0,
            "duplication_risk": 0,
            "promotion_safety": 10,
        },
        "noise": noise,
        "acceptance_recommendation": "reject",
        "reasons": [reason],
        "limitations": limitations,
    }


def acceptance_recommendation(bucket: str, score: int, *, min_quality_score: int = 50, allow_review_required: bool = False) -> str:
    if bucket == "reject":
        return "reject"
    if bucket == "review_required":
        return "persist_candidate" if allow_review_required else "review_required"
    if score < min_quality_score:
        return "reject"
    if bucket in PERSIST_BUCKETS:
        return "persist_candidate"
    return "reject"


def score_candidates(
    candidates: list[dict[str, Any]],
    *,
    min_quality_score: int = 50,
    allow_review_required: bool = False,
) -> list[dict[str, Any]]:
    return [
        score_semantic_candidate(candidate, min_quality_score=min_quality_score, allow_review_required=allow_review_required)
        for candidate in candidates
    ]


def attach_quality_to_candidate(
    candidate: dict[str, Any],
    *,
    min_quality_score: int = 50,
    allow_review_required: bool = False,
) -> dict[str, Any]:
    quality = score_semantic_candidate(candidate, min_quality_score=min_quality_score, allow_review_required=allow_review_required)
    updated = dict(candidate)
    updated["quality"] = quality
    payload = dict(updated.get("payload") or {})
    payload["quality"] = quality
    updated["payload"] = payload
    updated["usable_for_promotion"] = False
    return updated


def filter_candidates_for_persistence(
    candidates: list[dict[str, Any]],
    *,
    min_quality_score: int = 50,
    allow_review_required: bool = False,
    reject_noisy: bool = True,
) -> dict[str, Any]:
    eligible = []
    rejected = []
    review_required = []
    scored = []
    for candidate in candidates:
        annotated = attach_quality_to_candidate(candidate, min_quality_score=min_quality_score, allow_review_required=allow_review_required)
        quality = annotated["quality"]
        noisy_reject = reject_noisy and (quality.get("noise") or {}).get("recommended_action") == "reject"
        basic_guard = all(
            [
                annotated.get("quoted_span"),
                annotated.get("source_url"),
                annotated.get("source_id"),
                annotated.get("chunk_id"),
                annotated.get("variable_type") != "unknown",
                not annotated.get("usable_for_promotion"),
            ]
        )
        if basic_guard and not noisy_reject and quality.get("acceptance_recommendation") == "persist_candidate":
            eligible.append(annotated)
        elif quality.get("acceptance_recommendation") == "review_required":
            review_required.append(annotated)
        else:
            rejected.append(annotated)
        scored.append(annotated)
    return {
        "scored_candidates": scored,
        "eligible_candidates": eligible,
        "review_required_candidates": review_required,
        "rejected_candidates": rejected,
        "quality_assessments": [candidate.get("quality") for candidate in scored],
    }


def summarize_quality(assessments: list[dict[str, Any]]) -> dict[str, Any]:
    buckets = Counter(item.get("quality_bucket") for item in assessments)
    recommendations = Counter(item.get("acceptance_recommendation") for item in assessments)
    noise = Counter()
    reject_reasons = Counter()
    for item in assessments:
        noise.update((item.get("noise") or {}).get("noise_types") or [])
        if item.get("acceptance_recommendation") in {"reject", "review_required"}:
            reject_reasons.update((item.get("noise") or {}).get("noise_types") or item.get("reasons") or ["quality_below_threshold"])
    return {
        "quality_distribution": {key: buckets.get(key, 0) for key in ["high_quality", "usable", "weak_but_usable", "review_required", "reject"]},
        "recommendation_distribution": dict(recommendations),
        "noise_distribution": dict(noise),
        "top_reject_reasons": [reason for reason, _ in reject_reasons.most_common(5)],
    }
