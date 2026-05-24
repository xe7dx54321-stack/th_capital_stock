#!/usr/bin/env python3
"""Thesis-aware field and evidence dependency helpers for Phase 13."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "00_control" / "thesis_evidence_requirements.json"

FIELD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def _unique(items: list[Any]) -> list[str]:
    return list(dict.fromkeys(str(item) for item in items if str(item or "").strip()))


def load_thesis_requirements(config_path: str | None = None) -> dict[str, Any]:
    """Load the thesis evidence requirement config.

    The config is intentionally data-driven so Phase 13 can calibrate gates
    without weakening the underlying promotion checks.
    """

    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    data.setdefault("thesis_requirements", {})
    data.setdefault("default_thesis_types", ["valuation_rerating"])
    return data


def _claim_text(claim: dict[str, Any]) -> str:
    return " ".join(
        str(claim.get(key) or "")
        for key in ("claim_text", "text", "claim_type", "theme", "stance")
    ).lower()


def infer_thesis_type_from_claims(claims: list[dict[str, Any]], report: dict[str, Any] | None = None) -> list[str]:
    """Infer thesis types from claim/report text using conservative keywords."""

    report = report or {}
    text = " ".join(
        [_claim_text(claim) for claim in (claims or [])]
        + [
            str(report.get("thesis_type") or ""),
            str(report.get("theme") or ""),
            str(report.get("primary_signal") or ""),
            str(report.get("confidence_rationale") or ""),
            str(report.get("action_detail") or ""),
            str(report.get("action") or ""),
        ]
    ).lower()
    inferred: list[str] = []
    keyword_map = [
        ("cash_flow_improvement", ("cash flow", "free cash flow", "fcf", "capex")),
        ("cloud_growth", ("cloud", "aliyun", "云", "cloud growth")),
        ("shareholder_return", ("buyback", "dividend", "shareholder return", "capital return")),
        ("revenue_growth", ("revenue growth", "sales growth", "top line")),
        ("margin_improvement", ("margin", "gross margin", "operating margin")),
        ("earnings_revision", ("earnings revision", "eps revision", "estimate revision")),
        ("balance_sheet_repair", ("balance sheet", "deleverag", "debt", "cash balance")),
        ("ai_infrastructure_demand", ("ai infrastructure", "gpu demand", "compute demand")),
        ("cost_reduction", ("cost reduction", "cost cut", "efficiency")),
        ("event_driven", ("event", "spin-off", "catalyst")),
        ("technical_momentum", ("momentum", "breakout", "technical")),
        ("valuation_rerating", ("valuation", "rerating", "multiple", "peer", "historical percentile")),
    ]
    for thesis_type, tokens in keyword_map:
        if any(token in text for token in tokens):
            inferred.append(thesis_type)
    if report.get("thesis_types"):
        inferred.extend(str(item) for item in report.get("thesis_types") or [])
    if report.get("thesis_type"):
        inferred.append(str(report.get("thesis_type")))
    return _unique(inferred or ["valuation_rerating"])


def get_required_fields_for_thesis(
    thesis_types: list[str],
    config: dict[str, Any] | None = None,
) -> dict[str, list[str]]:
    """Return core/supporting/optional fields for the union of thesis types.

    Core wins over supporting, and supporting wins over optional. That keeps a
    field such as capex correctly blocking for cash-flow theses even if another
    thesis treats it as optional.
    """

    config = config or load_thesis_requirements()
    requirements = config.get("thesis_requirements") or {}
    known_thesis = [item for item in _unique(thesis_types or config.get("default_thesis_types") or []) if item in requirements]
    if not known_thesis:
        known_thesis = _unique(config.get("default_thesis_types") or ["valuation_rerating"])
    core: list[str] = []
    supporting: list[str] = []
    optional: list[str] = []
    required_evidence_types: list[str] = []
    required_bear_case_responses: list[str] = []
    for thesis_type in known_thesis:
        item = requirements.get(thesis_type) or {}
        core.extend(item.get("core_fields") or [])
        supporting.extend(item.get("supporting_fields") or [])
        optional.extend(item.get("optional_fields") or [])
        required_evidence_types.extend(item.get("required_evidence_types") or [])
        required_bear_case_responses.extend(item.get("required_bear_case_responses") or [])

    core = _unique(core)
    supporting = [field for field in _unique(supporting) if field not in set(core)]
    optional = [field for field in _unique(optional) if field not in set(core) and field not in set(supporting)]
    return {
        "thesis_types": known_thesis,
        "core_fields": core,
        "supporting_fields": supporting,
        "optional_fields": optional,
        "required_evidence_types": _unique(required_evidence_types),
        "required_bear_case_responses": _unique(required_bear_case_responses),
    }


def _field_from_issue(issue: Any) -> str | None:
    if isinstance(issue, dict):
        fields = issue.get("affected_fields") or []
        if fields:
            return str(fields[0])
        if issue.get("field"):
            return str(issue.get("field"))
        code = str(issue.get("code") or "")
    else:
        code = str(issue or "")
    if ":" in code:
        return code.split(":", 1)[1]
    if FIELD_RE.match(code):
        return code
    return None


def _missing_reason_for(field: str, field_details: dict[str, Any]) -> str:
    detail = field_details.get(field) or {}
    return str(detail.get("missing_reason") or detail.get("reason") or "FIELD_NOT_FOUND")


def classify_missing_fields(
    missing_fields: list[Any],
    thesis_types: list[str],
    field_details: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify missing fields as core/supporting/optional/unknown for theses."""

    field_details = field_details or {}
    dependencies = get_required_fields_for_thesis(thesis_types, config=config)
    core = set(dependencies["core_fields"])
    supporting = set(dependencies["supporting_fields"])
    optional = set(dependencies["optional_fields"])
    buckets = {
        "core_missing": [],
        "supporting_missing": [],
        "optional_missing": [],
        "unknown_missing": [],
    }
    details: dict[str, dict[str, Any]] = {}
    for item in missing_fields or []:
        field = _field_from_issue(item)
        if not field:
            continue
        field = str(field)
        if field in core:
            bucket = "core_missing"
        elif field in supporting:
            bucket = "supporting_missing"
        elif field in optional:
            bucket = "optional_missing"
        else:
            bucket = "unknown_missing"
        if field not in buckets[bucket]:
            buckets[bucket].append(field)
        details[field] = {
            "classification": bucket,
            "reason": _missing_reason_for(field, field_details),
            "dependency": bucket.replace("_missing", ""),
        }
    for key in buckets:
        buckets[key] = sorted(buckets[key])
    return {
        **buckets,
        "field_dependency": dependencies,
        "field_details": details,
    }


def _warning(field: str, reason: str, classification: str, thesis_types: list[str]) -> dict[str, Any]:
    impact = {
        "core_missing": f"required core field for {', '.join(thesis_types)} thesis",
        "supporting_missing": f"supporting field gap for {', '.join(thesis_types)} thesis",
        "optional_missing": f"not core to {', '.join(thesis_types)} thesis",
        "unknown_missing": "field dependency is not configured for this thesis",
    }.get(classification, "field dependency warning")
    return {
        "field": field,
        "reason": reason,
        "classification": classification,
        "impact": impact,
    }


def build_promotion_evidence_gate(
    *,
    ticker: str,
    thesis_types: list[str],
    missing_fields: list[Any],
    field_details: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the Phase 13 core vs non-core promotion evidence gate."""

    config = config or load_thesis_requirements()
    dependencies = get_required_fields_for_thesis(thesis_types, config=config)
    thesis_types = dependencies["thesis_types"]
    classification = classify_missing_fields(missing_fields, thesis_types, field_details or {}, config=config)
    details = classification.get("field_details") or {}
    core_blockers = [
        _warning(field, (details.get(field) or {}).get("reason") or "FIELD_NOT_FOUND", "core_missing", thesis_types)
        for field in classification["core_missing"]
    ]
    supporting_warnings = [
        _warning(field, (details.get(field) or {}).get("reason") or "FIELD_NOT_FOUND", "supporting_missing", thesis_types)
        for field in classification["supporting_missing"]
    ]
    optional_warnings = [
        _warning(field, (details.get(field) or {}).get("reason") or "FIELD_NOT_FOUND", "optional_missing", thesis_types)
        for field in classification["optional_missing"]
    ]
    unknown_warnings = [
        _warning(field, (details.get(field) or {}).get("reason") or "FIELD_NOT_FOUND", "unknown_missing", thesis_types)
        for field in classification["unknown_missing"]
    ]
    if core_blockers:
        gate_status = "blocked"
    elif unknown_warnings:
        gate_status = "needs_manual_review"
    elif supporting_warnings or optional_warnings:
        gate_status = "pass_with_warnings"
    else:
        gate_status = "pass"
    return {
        "ticker": ticker.upper(),
        "thesis_types": thesis_types,
        "field_dependency": {
            "core_fields": dependencies["core_fields"],
            "supporting_fields": dependencies["supporting_fields"],
            "optional_fields": dependencies["optional_fields"],
        },
        "missing_field_classification": {
            "core_missing": classification["core_missing"],
            "supporting_missing": classification["supporting_missing"],
            "optional_missing": classification["optional_missing"],
            "unknown_missing": classification["unknown_missing"],
        },
        "core_blockers": core_blockers,
        "supporting_warnings": supporting_warnings,
        "optional_warnings": optional_warnings,
        "unknown_warnings": unknown_warnings,
        "gate_status": gate_status,
    }


def gate_to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))
    except TypeError:
        return {}
