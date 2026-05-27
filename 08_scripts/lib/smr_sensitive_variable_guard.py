#!/usr/bin/env python3
"""Sensitive variable guardrails for Phase 31 evidence governance."""

from __future__ import annotations

from typing import Any


SENSITIVE_VARIABLES = {
    "supplier_share",
    "supplier_share_signal",
    "ASP_price_proxy",
    "ASP_price_signal",
    "customer_allocation_proxy",
    "customer_allocation_signal",
    "official_consensus",
    "confirmed_order",
    "order_visibility_signal",
}

FORBIDDEN_CONFIRMED_UPGRADES = {
    "upgrade_to_confirmed_supplier_share",
    "upgrade_to_confirmed_ASP",
    "upgrade_to_confirmed_customer_allocation",
    "upgrade_to_official_consensus",
    "allow_promotion",
    "create_pending",
    "create_paper_order",
}


def is_sensitive_variable(variable_type: str | None) -> bool:
    return str(variable_type or "") in SENSITIVE_VARIABLES


def max_allowed_usage_for_sensitive(candidate: dict[str, Any]) -> str:
    direct = bool(((candidate.get("payload") or {}).get("quality") or {}).get("quality_bucket") == "high_quality")
    return "scenario_analysis_only" if not direct else "scenario_analysis_only"


def guard_sensitive_variable(candidate: dict[str, Any], *, action: str | None = None) -> dict[str, Any]:
    variable_type = str(candidate.get("variable_type") or "")
    sensitive = is_sensitive_variable(variable_type)
    action = str(action or "")
    violations: list[str] = []
    blocked_confirmed_upgrade = False
    manual_review_required = False

    if action in FORBIDDEN_CONFIRMED_UPGRADES:
        violations.append(f"forbidden action: {action}")
        blocked_confirmed_upgrade = True
    if bool(candidate.get("usable_for_promotion")):
        violations.append("semantic evidence cannot be usable_for_promotion")
    if sensitive:
        manual_review_required = True
        if str(candidate.get("evidence_status") or "") == "confirmed":
            violations.append("semantic evidence cannot confirm sensitive variable")
            blocked_confirmed_upgrade = True
        if variable_type in {"official_consensus"} and str(candidate.get("source_type") or "").lower() != "official_consensus_provider":
            violations.append("internal proxy cannot be official consensus")
            blocked_confirmed_upgrade = True
        if variable_type == "confirmed_order" or str(candidate.get("evidence_status") or "") == "confirmed":
            payload = candidate.get("payload") or {}
            extraction = ((payload.get("gate") or {}).get("extraction") or {})
            if str(extraction.get("evidence_strength") or "").lower() == "management_commentary":
                violations.append("management commentary cannot be confirmed order")
                blocked_confirmed_upgrade = True
        if str(candidate.get("allowed_usage") or "") not in {"scenario_analysis_only", "context_only", "blocked", "planned_only"}:
            violations.append("sensitive variable allowed_usage too permissive")

    return {
        "evidence_id": candidate.get("evidence_id"),
        "ticker": candidate.get("ticker"),
        "variable_type": variable_type,
        "is_sensitive": sensitive,
        "manual_review_required": manual_review_required,
        "blocked_confirmed_upgrade": blocked_confirmed_upgrade,
        "violations": violations,
        "allowed_usage_cap": "scenario_analysis_only" if sensitive else candidate.get("allowed_usage"),
        "promotion_allowed": False,
    }


def guard_candidates(candidates: list[dict[str, Any]], *, action: str | None = None) -> list[dict[str, Any]]:
    return [guard_sensitive_variable(candidate, action=action) for candidate in candidates]


def summarize_sensitive_guard(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sensitive_items_checked": sum(1 for row in results if row.get("is_sensitive")),
        "blocked_confirmed_upgrades": sum(1 for row in results if row.get("blocked_confirmed_upgrade")),
        "manual_review_required": sum(1 for row in results if row.get("manual_review_required")),
        "violations": sum(len(row.get("violations") or []) for row in results),
    }
