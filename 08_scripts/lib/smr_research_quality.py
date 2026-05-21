#!/usr/bin/env python3
"""Deterministic evidence checker and report linter for SMR research outputs."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Literal

from smr_data_health import gate_to_dict
from smr_source_registry import source_registry_snapshot


@dataclass
class Claim:
    claim_id: str
    text: str
    claim_type: str
    importance: Literal["core", "supporting", "background"]
    related_ticker: str | None = None
    related_theme: str | None = None


@dataclass
class EvidenceItem:
    evidence_id: str
    source_key: str
    source_type: str
    source_quality: Literal["primary", "secondary", "tertiary", "weak"]
    published_at: datetime | None
    text: str
    url_or_doc_id: str | None
    supports_claim: bool
    strength: float


@dataclass
class ClaimEvidenceResult:
    passed: bool
    severity: Literal["pass", "warn", "degrade", "block"]
    claim: Claim
    evidence_count: int
    primary_or_secondary_count: int
    independent_source_count: int
    reasons: list[str]


@dataclass
class ReportEvidenceResult:
    passed: bool
    severity: Literal["pass", "warn", "degrade", "block"]
    unsupported_core_claims: list[dict[str, Any]]
    weak_claims: list[dict[str, Any]]
    missing_counter_evidence: bool
    missing_primary_sources: bool
    recommendation_allowed: bool
    reasons: list[str]
    evidence_summary: dict[str, Any]


@dataclass
class LintIssue:
    severity: Literal["info", "warn", "error", "blocker"]
    code: str
    message: str
    location: str | None = None
    suggested_fix: str | None = None


@dataclass
class ReportLintResult:
    passed: bool
    max_severity: str
    issues: list[dict[str, Any]]
    allowed_publish_status: Literal[
        "draft",
        "candidate_shadow",
        "observation_only",
        "human_review_required",
        "blocked",
    ]


ACTION_PATTERN = re.compile(r"(建议)?(买入|加仓|卖出|减仓|调入|调出|建仓|buy|add|sell|reduce)", re.I)
STRONG_CLAIM_PATTERN = re.compile(r"(确定性很强|显著受益|产业链验证充分|估值便宜|市场预期(?:已经)?(?:上修|下修)|一致预期(?:已经)?(?:上调|下调))")
PLACEHOLDER_PATTERNS = ["TBD", "待补充", "这里填写", "占位", "暂无", "TODO"]
CONSENSUS_CLAIM_PATTERN = re.compile(r"(市场预期(?:已经)?(?:上修|下修)|一致预期(?:已经)?(?:上调|下调)|estimate revision|consensus revision)", re.I)


def strip_model_output(text: str | None) -> str:
    raw = str(text or "").strip()
    marker = "## Model Output"
    if marker in raw:
        return raw.split(marker, 1)[1].strip()
    return raw


def report_has_action(report_text: str | None, dashboard_summary: dict[str, Any] | None = None) -> bool:
    text = strip_model_output(report_text)
    summary = dashboard_summary or {}
    action_text = " ".join(
        str(summary.get(key) or "")
        for key in ("action", "action_detail", "portfolio_action_plan")
    )
    return bool(ACTION_PATTERN.search(text) or ACTION_PATTERN.search(action_text))


def has_bear_case(text: str) -> bool:
    return any(token in text for token in ("反方", "Bear", "bear", "风险与证伪", "证伪", "attack", "Attack"))


def has_kill_conditions(text: str) -> bool:
    return any(token in text for token in ("证伪", "失效", "kill", "止损", "退出", "触发器"))


def has_position_sizing(text: str, dashboard_summary: dict[str, Any] | None = None) -> bool:
    summary = dashboard_summary or {}
    if summary.get("portfolio_action_plan"):
        return True
    return bool(re.search(r"(仓位|万元|%|pct|position)", text, flags=re.I))


def evidence_summary_from_pack(evidence_pack_text: str | None) -> dict[str, Any]:
    text = str(evidence_pack_text or "")
    source_path_count = 0
    match = re.search(r"source_path_count:\s*`?(\d+)`?", text)
    if match:
        source_path_count = int(match.group(1))
    else:
        source_path_count = len(set(re.findall(r"(?:0[0-9]_|1[0-9]_)[^\s`|)]+", text)))
    primary_terms = ["官方公告", "巨潮", "SEC", "公司 IR", "业绩材料", "official", "filing", "公告/IR"]
    secondary_terms = ["电话会", "transcript", "公开电话会"]
    tertiary_terms = ["研报", "新闻", "MarketScreener"]
    return {
        "source_path_count": source_path_count,
        "primary_anchor_count": sum(text.count(term) for term in primary_terms),
        "secondary_anchor_count": sum(text.count(term) for term in secondary_terms),
        "tertiary_anchor_count": sum(text.count(term) for term in tertiary_terms),
        "has_evidence_chain": "证据链" in text or "Evidence" in text or "Evidence Clip" in text,
    }


def check_claim_evidence(claim: Claim, evidence_items: list[EvidenceItem]) -> ClaimEvidenceResult:
    supporting = [item for item in evidence_items if item.supports_claim and item.strength > 0]
    primary_or_secondary = [item for item in supporting if item.source_quality in {"primary", "secondary"}]
    independent_sources = {item.source_key for item in supporting if item.source_key}
    reasons = []
    if claim.importance == "core" and not supporting:
        reasons.append("核心 claim 没有任何 evidence_id 支撑。")
    if claim.importance == "core" and len(primary_or_secondary) < 1:
        reasons.append("核心 claim 缺少 primary/secondary 证据。")
    if claim.importance == "core" and len(independent_sources) < 2:
        reasons.append("核心 claim 独立来源不足 2 个。")
    severity: Literal["pass", "warn", "degrade", "block"] = "pass"
    if claim.importance == "core" and not supporting:
        severity = "block"
    elif reasons:
        severity = "degrade"
    return ClaimEvidenceResult(
        passed=not reasons,
        severity=severity,
        claim=claim,
        evidence_count=len(supporting),
        primary_or_secondary_count=len(primary_or_secondary),
        independent_source_count=len(independent_sources),
        reasons=reasons,
    )


def check_report_evidence(
    report_text: str | None,
    dashboard_summary: dict[str, Any] | None = None,
    evidence_pack_text: str | None = None,
    claims: list[Claim] | None = None,
    evidence_items: list[EvidenceItem] | None = None,
) -> ReportEvidenceResult:
    text = strip_model_output(report_text)
    summary = dashboard_summary or {}
    evidence_summary = evidence_summary_from_pack(evidence_pack_text)
    action = report_has_action(text, summary)
    counter = has_bear_case(text)
    primary_count = evidence_summary.get("primary_anchor_count") or 0
    source_count = evidence_summary.get("source_path_count") or 0
    reasons = []
    unsupported_core: list[dict[str, Any]] = []
    weak_claims: list[dict[str, Any]] = []
    severity: Literal["pass", "warn", "degrade", "block"] = "pass"

    for claim in claims or []:
        result = check_claim_evidence(claim, evidence_items or [])
        if not result.passed and claim.importance == "core":
            unsupported_core.append(asdict(result))
        elif not result.passed:
            weak_claims.append(asdict(result))

    if unsupported_core:
        reasons.append("存在核心 claim 无足够证据。")
        severity = "block"
    if action and not counter:
        reasons.append("交易候选缺少反方观点或证伪段落。")
        severity = "block"
    if action and primary_count < 1:
        reasons.append("交易候选缺少一手/primary 来源锚点。")
        if severity != "block":
            severity = "degrade"
    if action and source_count < 4:
        reasons.append("交易候选来源数量不足 4 个。")
        if severity == "pass":
            severity = "degrade"
    if not action and source_count < 1:
        reasons.append("报告没有可追溯证据包来源。")
        if severity == "pass":
            severity = "warn"

    return ReportEvidenceResult(
        passed=severity in {"pass", "warn"},
        severity=severity,
        unsupported_core_claims=unsupported_core,
        weak_claims=weak_claims,
        missing_counter_evidence=action and not counter,
        missing_primary_sources=action and primary_count < 1,
        recommendation_allowed=action and severity in {"pass", "warn"},
        reasons=reasons,
        evidence_summary=evidence_summary,
    )


def issue(severity: str, code: str, message: str, location: str | None = None, suggested_fix: str | None = None) -> LintIssue:
    return LintIssue(severity=severity, code=code, message=message, location=location, suggested_fix=suggested_fix)


def max_severity(issues: list[LintIssue]) -> str:
    rank = {"info": 0, "warn": 1, "error": 2, "blocker": 3}
    if not issues:
        return "info"
    return max((item.severity for item in issues), key=lambda value: rank.get(value, 0))


def lint_report(
    report_text: str | None,
    dashboard_summary: dict[str, Any] | None = None,
    freshness_gate_result: Any = None,
    evidence_check_result: ReportEvidenceResult | dict[str, Any] | None = None,
    source_snapshot: dict[str, Any] | None = None,
) -> ReportLintResult:
    text = strip_model_output(report_text)
    summary = dashboard_summary or {}
    gate = gate_to_dict(freshness_gate_result)
    evidence = asdict(evidence_check_result) if isinstance(evidence_check_result, ReportEvidenceResult) else (evidence_check_result or {})
    src_snapshot = source_snapshot or source_registry_snapshot()
    issues: list[LintIssue] = []
    action = report_has_action(text, summary)

    for token in PLACEHOLDER_PATTERNS:
        if token in text:
            issues.append(issue("blocker", "placeholder_text", f"报告包含占位/未完成文本：{token}", suggested_fix="删除占位文本并补齐真实内容。"))
    if action and gate.get("status") == "block":
        issues.append(issue("blocker", "action_with_stale_data", "数据新鲜度门禁未通过，不能输出买入/卖出/加仓/减仓候选。", suggested_fix="改为 observation_only 或先修复数据。"))
    elif action and gate.get("status") == "degrade":
        issues.append(issue("warn", "action_with_degraded_data", "数据新鲜度为 degraded，交易动作只能作为候选观察或人审前材料，不能直接升级为正式结论。", suggested_fix="补齐降级数据或明确 proxy/缺口。"))
    if CONSENSUS_CLAIM_PATTERN.search(text):
        disabled_consensus = any(
            item.get("source_key") == "consensus_revision" or item.get("data_type") == "expectation"
            for item in src_snapshot.get("disabled_or_planned") or []
        )
        proxy_wording = any(token in text for token in ("内部代理", "预期修正代理", "proxy", "Proxy"))
        official_strong_wording = any(token in text for token in ("一致预期已经", "市场预期已经", "official consensus"))
        if disabled_consensus and (official_strong_wording or not proxy_wording):
            issues.append(issue("blocker", "consensus_claim_without_source", "consensus_revision 当前 planned/disabled，报告不能声称市场预期已上修或下修。", suggested_fix="改写为缺少一致预期数据，暂无法验证预期修正。"))
    if STRONG_CLAIM_PATTERN.search(text) and (evidence.get("severity") in {"block", "degrade"}):
        issues.append(issue("error", "strong_claim_weak_evidence", "报告含强结论，但证据检查未通过。", suggested_fix="降级为待补证据或补齐来源。"))
    if action and not (has_bear_case(text) or summary.get("bear_case_summary") or summary.get("bear_case_result")):
        issues.append(issue("blocker", "missing_bear_case", "交易候选缺少反方观点。", suggested_fix="补充反方观点、风险与证伪。"))
    if action and not (has_kill_conditions(text) or summary.get("kill_triggers")):
        issues.append(issue("blocker", "missing_kill_conditions", "交易候选缺少失效/证伪/退出条件。", suggested_fix="补充 kill triggers。"))
    if action and not has_position_sizing(text, summary):
        issues.append(issue("blocker", "missing_position_sizing", "交易候选缺少仓位或金额口径。", suggested_fix="补充初始仓位、加仓和减仓条件。"))
    if action and not any(token in text for token in ("风险", "不确定", "证伪")):
        issues.append(issue("blocker", "missing_risk_section", "交易候选缺少风险提示。", suggested_fix="补充风险与证伪。"))

    severity = max_severity(issues)
    if severity == "blocker":
        allowed = "blocked"
    elif action and gate.get("status") in {"pass", "warn"}:
        allowed = "human_review_required"
    elif gate.get("status") in {"degrade", "block"}:
        allowed = "observation_only"
    else:
        allowed = "candidate_shadow"
    return ReportLintResult(
        passed=severity not in {"error", "blocker"},
        max_severity=severity,
        issues=[asdict(item) for item in issues],
        allowed_publish_status=allowed,
    )


def quality_to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))
