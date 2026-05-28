#!/usr/bin/env python3
"""Validate Phase 42 manual source intake payloads."""

from __future__ import annotations

from typing import Any

from smr_manual_source_intake import INTAKE_SOURCE_TYPES


AUTHORIZED_CONSENSUS_TYPES = {"authorized_consensus_source", "sell_side_authorized_note"}
DIRECT_SUPPLIER_TYPES = {"company_direct_disclosure", "customer_direct_disclosure"}
DIRECT_ALLOCATION_TYPES = {"company_direct_disclosure", "customer_side_public_statement"}


SAMPLE_FIXTURES: dict[str, dict[str, Any]] = {
    "official_consensus": {
        "source_type": "authorized_consensus_source",
        "source_title": "Authorized consensus snapshot",
        "source_provider": "authorized_provider",
        "source_date": "2026-05-28",
        "source_url_or_reference": "licensed-terminal-reference",
        "permission_status": "authorized_or_user_provided",
        "quoted_span": "Authorized provider consensus summary for manual research review.",
        "evidence_type": "official_consensus",
        "allowed_usage_requested": "expectation_gap_benchmark",
        "limitations": ["licensed data; store metadata only"],
        "user_notes": "sample fixture only",
    },
    "official_consensus_internal_proxy": {
        "source_type": "proxy_evidence_note",
        "source_title": "Internal proxy",
        "source_provider": "internal_model",
        "source_date": "2026-05-28",
        "source_url_or_reference": "",
        "permission_status": "internal_only",
        "quoted_span": "Internal proxy suggests estimate direction.",
        "evidence_type": "official_consensus",
        "allowed_usage_requested": "expectation_gap_benchmark",
        "limitations": [],
        "user_notes": "must be rejected",
    },
    "supplier_share_scenario": {
        "source_type": "scenario_assumption",
        "source_title": "Supplier share scenario",
        "source_provider": "manual_research",
        "source_date": "2026-05-28",
        "source_url_or_reference": "",
        "permission_status": "authorized_or_user_provided",
        "quoted_span": "Scenario assumption for sensitivity only.",
        "evidence_type": "supplier_share",
        "allowed_usage_requested": "scenario_analysis_only",
        "limitations": ["not confirmed"],
        "user_notes": "scenario fixture",
    },
    "customer_allocation_proxy": {
        "source_type": "proxy_evidence_note",
        "source_title": "Customer allocation proxy",
        "source_provider": "manual_research",
        "source_date": "2026-05-28",
        "source_url_or_reference": "",
        "permission_status": "authorized_or_user_provided",
        "quoted_span": "Proxy evidence references customer demand but not allocation.",
        "evidence_type": "confirmed_customer_allocation",
        "allowed_usage_requested": "bear_case_context_or_scenario_support",
        "limitations": ["proxy only"],
        "user_notes": "proxy fixture",
    },
}


def sample_intake(name: str) -> dict[str, Any]:
    if name not in SAMPLE_FIXTURES:
        raise ValueError(f"Unsupported sample intake fixture: {name}")
    return dict(SAMPLE_FIXTURES[name])


def _has_text(value: Any) -> bool:
    return bool(str(value or "").strip())


def validate_manual_source_intake(payload: dict[str, Any]) -> dict[str, Any]:
    evidence_type = str(payload.get("evidence_type") or "")
    source_type = str(payload.get("source_type") or "")
    permission = str(payload.get("permission_status") or "")
    blocked: list[str] = []
    reasons: list[str] = []
    allowed_usage = "blocked"
    can_create_candidate = False
    can_be_confirmed = False

    if source_type not in INTAKE_SOURCE_TYPES and source_type not in {"customer_direct_disclosure"}:
        blocked.append("unsupported_source_type")
    if not _has_text(payload.get("quoted_span")):
        blocked.append("quoted_span_required")
    if not _has_text(payload.get("source_date")):
        blocked.append("source_date_required")

    if evidence_type == "official_consensus":
        allowed_usage = "expectation_gap_benchmark_if_authorized"
        if source_type not in AUTHORIZED_CONSENSUS_TYPES:
            blocked.append("official_consensus_requires_authorized_source")
        if permission != "authorized_or_user_provided":
            blocked.append("authorized_permission_required")
        if not _has_text(payload.get("source_provider")):
            blocked.append("source_provider_required")
        if not blocked:
            reasons.extend(["authorized source metadata present", "quoted span present"])
            can_create_candidate = True
    elif evidence_type == "supplier_share":
        if source_type == "scenario_assumption":
            allowed_usage = "scenario_analysis_only"
            if not blocked:
                reasons.extend(["scenario assumption provided", "scenario is not confirmed supplier share"])
                can_create_candidate = True
        elif source_type in DIRECT_SUPPLIER_TYPES:
            allowed_usage = "research_evidence_if_directly_disclosed"
            if not blocked:
                reasons.append("direct disclosure source route present")
                can_create_candidate = True
                can_be_confirmed = True
        elif source_type == "manual_channel_check_note":
            allowed_usage = "manual_context_only"
            if not blocked:
                reasons.append("manual channel check is context only")
                can_create_candidate = True
        else:
            blocked.append("supplier_share_source_route_not_sufficient")
    elif evidence_type == "confirmed_customer_allocation":
        if source_type in DIRECT_ALLOCATION_TYPES:
            allowed_usage = "research_evidence_if_directly_disclosed"
            if not blocked:
                reasons.append("direct allocation source route present")
                can_create_candidate = True
                can_be_confirmed = True
        elif source_type == "proxy_evidence_note":
            allowed_usage = "bear_case_context_or_scenario_support"
            if not blocked:
                reasons.extend(["proxy evidence note present", "proxy is not confirmed allocation"])
                can_create_candidate = True
        else:
            blocked.append("customer_allocation_requires_direct_or_proxy_route")
    else:
        blocked.append("unsupported_evidence_type")

    if can_be_confirmed and source_type in {"scenario_assumption", "proxy_evidence_note", "manual_channel_check_note"}:
        can_be_confirmed = False
        blocked.append("non_direct_source_cannot_be_confirmed")

    input_valid = not blocked
    return {
        "validation_result": {
            "evidence_type": evidence_type,
            "source_type": source_type,
            "input_valid": input_valid,
            "can_create_evidence_candidate": bool(input_valid and can_create_candidate),
            "can_be_confirmed": bool(input_valid and can_be_confirmed),
            "allowed_usage": allowed_usage if input_valid else "blocked",
            "reasons": reasons,
            "blocked_reasons": blocked,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_allowed": False,
        },
        "safety": {
            "validator_only": True,
            "evidence_written": False,
            "manual_input_auto_confirmed": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }
