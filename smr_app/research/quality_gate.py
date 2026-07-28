from __future__ import annotations

from typing import Any

from .claim_compiler import FORBIDDEN_CONCLUSION_PATTERN


def _claim_rejection_reasons(packet: dict[str, Any], claim: dict[str, Any]) -> list[str]:
    reasons = []
    usable = set(packet["quality"].get("usable_evidence_ids") or [])
    quarantined = set(packet["quality"].get("quarantined_fields") or [])
    evidence_ids = set(claim.get("evidence_ids") or [])
    source_paths = set(claim.get("source_paths") or [])
    if claim.get("requires_evidence", True) and not evidence_ids:
        reasons.append("missing_evidence")
    if evidence_ids - usable:
        reasons.append("unknown_evidence_id")
    if source_paths & quarantined:
        reasons.append("quarantined_source_field")
    if FORBIDDEN_CONCLUSION_PATTERN.search(str(claim.get("statement") or "")):
        reasons.append("forbidden_conclusion")
    return reasons


def evaluate_stock_research_quality(packet: dict[str, Any]) -> dict[str, Any]:
    approved = []
    rejected = []
    for claim in packet.get("claims") or []:
        reasons = _claim_rejection_reasons(packet, claim)
        if reasons:
            rejected.append({**claim, "reasons": reasons})
        else:
            approved.append(claim)

    usable = set(packet["quality"].get("usable_evidence_ids") or [])
    approved_scenarios = []
    rejected_scenarios = []
    for scenario in packet.get("scenarios") or []:
        unknown = [value for value in scenario.get("evidence_ids") or [] if value not in usable]
        if unknown:
            rejected_scenarios.append({**scenario, "reasons": ["unknown_evidence_id"]})
        else:
            approved_scenarios.append(scenario)

    readiness = packet["quality"].get("readiness") or "cannot_conclude"
    substantive = [claim for claim in approved if claim.get("category") != "investigation"]
    if not substantive or readiness == "cannot_conclude":
        report_status = "cannot_conclude"
    elif readiness == "research_ready" and not rejected and not rejected_scenarios:
        report_status = "research_ready"
    else:
        report_status = "evidence_limited"
    if not substantive:
        citation_coverage = None
    else:
        citation_coverage = 1.0 if all(claim.get("evidence_ids") for claim in substantive) else 0.0
    return {
        "gate_status": "passed",
        "report_status": report_status,
        "approved_claims": approved,
        "approved_claim_ids": [claim["claim_id"] for claim in approved],
        "rejected_claims": rejected,
        "rejected_claim_ids": [claim.get("claim_id") for claim in rejected],
        "approved_scenarios": approved_scenarios,
        "rejected_scenarios": rejected_scenarios,
        "citation_coverage": citation_coverage,
        "quarantined_field_leaks": [],
    }
