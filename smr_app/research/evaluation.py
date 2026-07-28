from __future__ import annotations

import re
from typing import Any

from .claim_compiler import FORBIDDEN_CONCLUSION_PATTERN


INTERNAL_TOKEN_PATTERN = re.compile(
    r"(?:hkex_announcement|sec_earnings_material|sec_filing_document|"
    r"fundamentals\.[a-z_]+|risk\.alerts|evidence_closure_failed|market_data_blocked)"
)
PRIMARY_SOURCE_TYPES = {"filing", "official_filing"}
PRIMARY_SOURCE_QUALITIES = {"primary", "official"}


def _finding(code: str, message: str, *, hard: bool = True) -> dict[str, Any]:
    return {"code": code, "message": message, "hard": hard}


def evaluate_stock_deep_dive_case(
    *,
    case: dict[str, Any],
    run: dict[str, Any],
    packet: dict[str, Any] | None,
    report: str | None,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    ticker = str(case["ticker"])
    if run.get("status") != "completed":
        findings.append(_finding("workflow_not_completed", f"工作流状态为 {run.get('status')}"))
    if not packet or not report:
        findings.append(_finding("artifact_missing", "研究数据包或报告产物缺失"))
        return _case_result(case, run, findings, packet)

    if packet.get("schema_version") != "2.0":
        findings.append(_finding("schema_mismatch", "研究数据包不是 2.0 版本"))
    if packet.get("ticker") != ticker:
        findings.append(_finding("ticker_mismatch", "报告标的与评测样本不一致"))

    quality = packet.get("quality") or {}
    report_gate = quality.get("report_gate") or {}
    status = report_gate.get("report_status") or quality.get("readiness")
    expected_statuses = set(case.get("expected_statuses") or [])
    if expected_statuses and status not in expected_statuses:
        findings.append(_finding("unexpected_report_status", f"报告状态 {status} 不在预期范围内"))
    for blocker in case.get("required_blockers") or []:
        if blocker not in (quality.get("blockers") or []):
            findings.append(_finding("required_blocker_missing", f"应识别的阻断项未出现：{blocker}"))

    validation = quality.get("report_validation") or {}
    if validation.get("status") != "passed":
        findings.append(_finding("report_validation_failed", "最终报告校验未通过"))

    claims = packet.get("claims") or []
    scenarios = packet.get("scenarios") or []
    usable = set(quality.get("usable_evidence_ids") or [])
    quarantined = set(quality.get("quarantined_fields") or [])
    items = {
        item.get("evidence_id"): item
        for item in (packet.get("datasets", {}).get("evidence", {}).get("items") or [])
    }
    min_claims = int(case.get("minimum_approved_claims", 0))
    max_claims = case.get("maximum_approved_claims")
    if len(claims) < min_claims:
        findings.append(_finding("insufficient_approved_claims", f"通过质量门的主张少于 {min_claims} 条"))
    if max_claims is not None and len(claims) > int(max_claims):
        findings.append(_finding("excess_approved_claims", f"通过质量门的主张多于 {max_claims} 条"))

    for claim in claims:
        claim_id = claim.get("claim_id") or "unknown"
        citations = set(claim.get("evidence_ids") or [])
        if not citations:
            findings.append(_finding("uncited_claim", f"主张 {claim_id} 没有引用"))
        if citations - usable:
            findings.append(_finding("unknown_claim_citation", f"主张 {claim_id} 引用了不可用证据"))
        if set(claim.get("source_paths") or []) & quarantined:
            findings.append(_finding("quarantined_field_leak", f"主张 {claim_id} 使用了隔离字段"))
        if FORBIDDEN_CONCLUSION_PATTERN.search(str(claim.get("statement") or "")):
            findings.append(_finding("unsupported_conclusion", f"主张 {claim_id} 含禁止性结论"))

    referenced = {evidence_id for claim in claims for evidence_id in claim.get("evidence_ids") or []}
    for evidence_id in referenced:
        item = items.get(evidence_id) or {}
        if item.get("source_type") not in PRIMARY_SOURCE_TYPES:
            findings.append(_finding("non_primary_source_type", f"核心证据 {evidence_id} 不是正式披露"))
        if item.get("source_quality") not in PRIMARY_SOURCE_QUALITIES:
            findings.append(_finding("non_primary_source_quality", f"核心证据 {evidence_id} 不是一手来源"))
        if not item.get("published_at"):
            findings.append(_finding("undated_core_evidence", f"核心证据 {evidence_id} 缺少发布日期"))

    blockers = set(quality.get("blockers") or [])
    directional = [scenario for scenario in scenarios if scenario.get("evidence_ids")]
    if "market_data_blocked" in blockers and status == "research_ready":
        findings.append(_finding("stale_data_promoted", "行情已过期但报告仍标记为可进入研究判断"))
    if status == "cannot_conclude" and claims:
        findings.append(_finding("claims_under_cannot_conclude", "无法判断状态下仍输出了事实主张"))
    if status != "research_ready" and directional:
        findings.append(_finding("directional_scenario_without_readiness", "证据未就绪时仍输出带引用的方向性情景"))

    judgments = [str(item.get("judgment") or "").strip() for item in scenarios]
    if len(judgments) == 3 and len(set(judgments)) != 3:
        findings.append(_finding("duplicated_scenarios", "三种情景的判断内容重复", hard=False))
    if INTERNAL_TOKEN_PATTERN.search(report):
        findings.append(_finding("internal_token_leak", "面向用户的报告泄露内部枚举或技术字段"))
    if "�" in report:
        findings.append(_finding("encoding_error", "报告包含乱码替换字符"))
    if len(report.strip()) < int(case.get("minimum_report_characters", 600)):
        findings.append(_finding("report_too_short", "报告内容过短，无法构成完整交付"))

    return _case_result(case, run, findings, packet)


def _case_result(
    case: dict[str, Any],
    run: dict[str, Any],
    findings: list[dict[str, Any]],
    packet: dict[str, Any] | None,
) -> dict[str, Any]:
    hard_findings = [item for item in findings if item["hard"]]
    soft_findings = [item for item in findings if not item["hard"]]
    penalty = 10 * len(hard_findings) + 2 * len(soft_findings)
    quality = (packet or {}).get("quality") or {}
    report_gate = quality.get("report_gate") or {}
    return {
        "ticker": case["ticker"],
        "market": case.get("market"),
        "role": case.get("role"),
        "run_id": run.get("run_id"),
        "workflow_status": run.get("status"),
        "report_status": report_gate.get("report_status") or quality.get("readiness"),
        "approved_claim_count": len((packet or {}).get("claims") or []),
        "usable_evidence_count": len(quality.get("usable_evidence_ids") or []),
        "quarantined_field_count": len(quality.get("quarantined_fields") or []),
        "score": max(0, 100 - penalty),
        "passed": not hard_findings,
        "findings": findings,
    }


def build_stock_deep_dive_scorecard(results: list[dict[str, Any]]) -> dict[str, Any]:
    hard_findings = [
        finding
        for result in results
        for finding in result.get("findings") or []
        if finding.get("hard")
    ]
    return {
        "case_count": len(results),
        "passed_case_count": sum(1 for result in results if result.get("passed")),
        "failed_case_count": sum(1 for result in results if not result.get("passed")),
        "average_score": round(sum(result.get("score", 0) for result in results) / len(results), 1) if results else 0.0,
        "research_ready_count": sum(1 for result in results if result.get("report_status") == "research_ready"),
        "evidence_limited_count": sum(1 for result in results if result.get("report_status") == "evidence_limited"),
        "cannot_conclude_count": sum(1 for result in results if result.get("report_status") == "cannot_conclude"),
        "hard_finding_count": len(hard_findings),
        "fact_integrity_error_count": sum(
            1 for item in hard_findings if item["code"] in {
                "quarantined_field_leak", "unknown_claim_citation", "non_primary_source_type",
                "non_primary_source_quality", "undated_core_evidence", "ticker_mismatch",
            }
        ),
        "unsupported_conclusion_count": sum(
            1 for item in hard_findings if item["code"] in {
                "unsupported_conclusion", "stale_data_promoted", "directional_scenario_without_readiness",
                "claims_under_cannot_conclude",
            }
        ),
        "quality_control_passed": bool(results) and not hard_findings,
        "passed": bool(results) and not hard_findings,
    }
