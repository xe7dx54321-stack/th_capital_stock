#!/usr/bin/env python3
"""Thesis-aware data-quality severity gate for Phase 13."""

from __future__ import annotations

import json
from typing import Any

from smr_thesis_dependency import build_promotion_evidence_gate


PASSING_STATUSES = {"pass", "pass_with_warnings", "degraded_non_core"}
BLOCKING_STATUSES = {"degraded_core", "blocked"}


def _field_from_root(root: Any) -> str | None:
    if isinstance(root, dict):
        fields = root.get("affected_fields") or []
        if fields:
            return str(fields[0])
        if root.get("field"):
            return str(root.get("field"))
        code = str(root.get("code") or "")
    else:
        code = str(root or "")
    if ":" in code:
        return code.split(":", 1)[1]
    return None


def _code_from_root(root: Any) -> str:
    if isinstance(root, dict):
        return str(root.get("code") or "DATA_QUALITY_RISK")
    return str(root or "DATA_QUALITY_RISK").split(":", 1)[0]


def _root_issue(root: Any, classification: str) -> dict[str, Any]:
    field = _field_from_root(root)
    return {
        "code": _code_from_root(root),
        "field": field,
        "classification": classification,
        "raw": root,
    }


def build_data_quality_gate(
    *,
    ticker: str,
    thesis_types: list[str],
    root_causes: list[Any] | None = None,
    field_quality: dict[str, Any] | None = None,
    before_status: str | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Reclassify data-quality root causes as core or non-core for a thesis."""

    root_causes = root_causes or []
    field_quality = field_quality or {}
    missing_fields = []
    for root in root_causes:
        field = _field_from_root(root)
        if field:
            missing_fields.append(field)
    for field, detail in field_quality.items():
        if detail.get("status") == "missing" and field not in missing_fields:
            missing_fields.append(field)
    field_gate = build_promotion_evidence_gate(
        ticker=ticker,
        thesis_types=thesis_types,
        missing_fields=missing_fields,
        field_details=field_quality,
        config=config,
    )
    classification = field_gate.get("missing_field_classification") or {}
    class_by_field = {
        field: "core_missing"
        for field in classification.get("core_missing") or []
    }
    class_by_field.update({field: "supporting_missing" for field in classification.get("supporting_missing") or []})
    class_by_field.update({field: "optional_missing" for field in classification.get("optional_missing") or []})
    class_by_field.update({field: "unknown_missing" for field in classification.get("unknown_missing") or []})

    core_issues: list[dict[str, Any]] = []
    non_core_issues: list[dict[str, Any]] = []
    unknown_issues: list[dict[str, Any]] = []
    for root in root_causes:
        field = _field_from_root(root)
        classification_name = class_by_field.get(field or "", "unknown_missing")
        issue = _root_issue(root, classification_name)
        if classification_name == "core_missing":
            core_issues.append(issue)
        elif classification_name == "unknown_missing":
            unknown_issues.append(issue)
        else:
            non_core_issues.append(issue)
    for field in missing_fields:
        if any(issue.get("field") == field for issue in [*core_issues, *non_core_issues, *unknown_issues]):
            continue
        classification_name = class_by_field.get(field, "unknown_missing")
        issue = {"code": "FIELD_NOT_FOUND", "field": field, "classification": classification_name}
        if classification_name == "core_missing":
            core_issues.append(issue)
        elif classification_name == "unknown_missing":
            unknown_issues.append(issue)
        else:
            non_core_issues.append(issue)

    if core_issues:
        status = "degraded_core"
        action_effect = "block_pending_review"
    elif unknown_issues:
        status = "blocked"
        action_effect = "needs_manual_review"
    elif non_core_issues:
        status = "degraded_non_core"
        action_effect = "reduce_confidence"
    elif before_status == "degraded":
        status = "pass_with_warnings"
        action_effect = "keep_status"
    else:
        status = "pass"
        action_effect = "keep_status"
    return {
        "ticker": ticker.upper(),
        "thesis_types": field_gate.get("thesis_types") or thesis_types,
        "before_status": before_status,
        "after_status": status,
        "status": status,
        "core_issues": core_issues,
        "non_core_issues": non_core_issues,
        "unknown_issues": unknown_issues,
        "field_gate": field_gate,
        "action_effect": action_effect,
        "promotion_blocking": status in BLOCKING_STATUSES,
    }


def data_quality_gate_to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))
    except TypeError:
        return {}
