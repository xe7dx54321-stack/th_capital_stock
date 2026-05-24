"""Field-level confidence scoring for fundamentals snapshots."""

from __future__ import annotations

from typing import Any


HIGH_QUALITY_SECTIONS = {
    "financial_statement",
    "balance_sheet",
    "income_statement",
    "cash_flow_statement",
    "management_discussion",
    "segment_performance",
    "liquidity_capital",
}


def confidence_level(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.60:
        return "medium"
    if score >= 0.40:
        return "low"
    return "blocked"


def _value_present(detail: dict[str, Any]) -> bool:
    return detail.get("extracted_value") is not None and not detail.get("missing_reason")


def _field_mapping_score(detail: dict[str, Any]) -> float:
    if detail.get("missing_reason") == "mapping_missing":
        return 0.2
    base = float(detail.get("confidence") or 0.0)
    if detail.get("method") in {"cross_listed_official_fundamentals", "factor_daily"}:
        base = max(base, 0.7)
    if detail.get("method") == "table_window":
        base = max(base, 0.55 if detail.get("extracted_value") is not None else 0.25)
    return max(0.0, min(base or 0.35, 1.0))


def _unit_score(detail: dict[str, Any]) -> float:
    warnings = set(detail.get("warnings") or [])
    if detail.get("unit_warning") in {"ambiguous_unit", "percentage_not_amount"} or "ambiguous_unit" in warnings:
        return min(float(detail.get("unit_confidence") or 0.25), 0.35)
    return max(float(detail.get("unit_confidence") or 0.0), 0.75 if detail.get("unit") or detail.get("currency") else 0.35)


def _source_score(detail: dict[str, Any], source_quality: str | None) -> float:
    if not detail.get("source_evidence_id"):
        return 0.25
    quality = str(source_quality or detail.get("source_quality") or "").lower()
    if quality == "primary":
        return 0.9
    if quality == "secondary":
        return 0.78
    return 0.72


def _section_score(detail: dict[str, Any]) -> float:
    section = str(detail.get("source_section_type") or detail.get("chunk_section_type") or "").lower()
    method = str(detail.get("method") or detail.get("extraction_method") or "").lower()
    if section in HIGH_QUALITY_SECTIONS:
        return 0.85
    if method in {"cross_listed_official_fundamentals", "factor_daily"}:
        return 0.76
    if detail.get("source_evidence_id"):
        return 0.68
    return 0.45


def _period_score(detail: dict[str, Any]) -> float:
    return 0.85 if detail.get("period") else 0.55


def _sanity_score(field: str, detail: dict[str, Any]) -> float:
    value = detail.get("extracted_value")
    if value is None:
        return 0.2
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.25
    if field in {"revenue", "gross_profit", "cash_and_equivalents", "shareholders_equity"} and numeric < 0:
        return 0.35
    if field in {"gross_margin", "operating_margin", "net_margin", "roe", "roic"} and abs(numeric) > 5:
        return 0.35
    if field in {"eps_basic", "eps_diluted"} and abs(numeric) > 10_000:
        return 0.25
    return 0.82


def score_fundamental_field(
    field: str,
    detail: dict[str, Any],
    *,
    source_quality: str | None = None,
) -> dict[str, Any]:
    """Return confidence, level, and allowed usage for a field detail."""

    detail = dict(detail or {})
    breakdown = {
        "field_mapping": round(_field_mapping_score(detail), 3),
        "unit": round(_unit_score(detail), 3),
        "source_evidence": round(_source_score(detail, source_quality), 3),
        "section_type": round(_section_score(detail), 3),
        "period_match": round(_period_score(detail), 3),
        "sanity_check": round(_sanity_score(field, detail), 3),
    }
    if detail.get("extraction_method") == "derived" or detail.get("method") == "derived":
        breakdown["derived_inputs"] = 0.85 if detail.get("input_evidence_ids") else 0.45
    weights = {
        "field_mapping": 0.22,
        "unit": 0.18,
        "source_evidence": 0.22,
        "section_type": 0.12,
        "period_match": 0.12,
        "sanity_check": 0.14,
        "derived_inputs": 0.12,
    }
    numerator = sum(breakdown[key] * weights.get(key, 0.0) for key in breakdown)
    denominator = sum(weights.get(key, 0.0) for key in breakdown)
    score = numerator / denominator if denominator else 0.0
    missing_reason = detail.get("missing_reason")
    if missing_reason:
        score = min(score, 0.35)
    score = round(max(0.0, min(score, 0.95)), 3)
    level = confidence_level(score)
    if not _value_present(detail):
        allowed_usage = "blocked"
    elif detail.get("unit_warning") in {"ambiguous_unit", "percentage_not_amount"} or "ambiguous_unit" in set(detail.get("warnings") or []):
        allowed_usage = "blocked"
    elif not detail.get("source_evidence_id"):
        allowed_usage = "context_only"
    elif score >= 0.75:
        allowed_usage = "promotion_evidence"
    elif score >= 0.60:
        allowed_usage = "supporting_evidence"
    elif score >= 0.40:
        allowed_usage = "context_only"
    else:
        allowed_usage = "blocked"
    return {
        "confidence": score,
        "confidence_breakdown": breakdown,
        "confidence_level": level,
        "allowed_usage": allowed_usage,
    }

