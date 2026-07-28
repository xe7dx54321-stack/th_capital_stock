from __future__ import annotations

import re
from typing import Any


CATEGORY_LABELS = {
    "source_material": "已核验材料",
    "fact": "可信事实",
    "change": "变化",
    "expectation_gap": "预期差边界",
    "catalyst": "潜在催化",
    "risk": "风险证据",
    "valuation": "估值事实",
}
STATUS_LABELS = {
    "research_ready": "可进入研究判断",
    "evidence_limited": "证据有限",
    "cannot_conclude": "暂无法判断",
}
MARKET_LABELS = {"A": "A 股", "H": "港股", "US": "美股"}
BLOCKER_LABELS = {
    "fundamentals_missing": "缺少基本面数据",
    "no_usable_evidence": "缺少可用于核心主张的一手证据",
    "missing_report_period": "报告期缺失或不明确",
    "net_income_revenue_conflict": "净利润与营业收入存在异常冲突",
    "gross_profit_revenue_conflict": "毛利润与营业收入存在异常冲突",
    "gross_margin_cross_field_conflict": "毛利率与基础字段存在异常冲突",
    "non_positive_revenue": "营业收入不是有效正数",
    "evidence_closure_failed": "字段与原始证据未形成闭环",
    "market_data_blocked": "行情数据新鲜度未达标",
}
SCENARIO_LABELS = {"bull": "乐观情景", "base": "基准情景", "bear": "谨慎情景"}
CITATION_PATTERN = re.compile(r"\[([A-Za-z0-9][A-Za-z0-9_.:-]{2,127})\]")


def _citations(evidence_ids: list[str]) -> str:
    return " ".join(f"[{evidence_id}]" for evidence_id in evidence_ids)


def _join_phrases(values: list[str]) -> str:
    cleaned = [str(value).strip().rstrip("。；") for value in values if str(value).strip()]
    return ("；".join(cleaned) + "。") if cleaned else "无。"


def compile_stock_research_report(packet: dict[str, Any], gate: dict[str, Any]) -> str:
    status = gate["report_status"]
    citation_coverage = gate.get("citation_coverage")
    citation_display = "不适用" if citation_coverage is None else f"{citation_coverage * 100:.0f}%"
    lines = [
        f"# 个股深度研究 V2 — {packet['ticker']}",
        "",
        f"- 市场：{MARKET_LABELS.get(packet['market'], packet['market'])}",
        f"- 研究状态：{STATUS_LABELS.get(status, status)}",
        f"- 可用证据：{len(packet['quality'].get('usable_evidence_ids') or [])} 条",
        f"- 已批准主张：{len(gate.get('approved_claims') or [])} 条",
        f"- 被拒绝主张：{len(gate.get('rejected_claims') or [])} 条",
        "",
    ]

    approved = gate.get("approved_claims") or []
    for category in ("source_material", "fact", "change", "expectation_gap", "catalyst", "risk", "valuation"):
        claims = [claim for claim in approved if claim.get("category") == category]
        if not claims:
            continue
        lines.extend([f"## {CATEGORY_LABELS[category]}", ""])
        for claim in claims:
            limitation = "；边界：" + " ".join(claim.get("limitations") or []) if claim.get("limitations") else ""
            lines.append(f"- {claim['statement']} {_citations(claim['evidence_ids'])}{limitation}")
        lines.append("")

    if not approved:
        lines.extend(["## 当前结论", "", "- 当前没有通过质量门的事实性主张，因此暂无法形成方向性判断。", ""])

    lines.extend(["## 三种情景", ""])
    for scenario in gate.get("approved_scenarios") or []:
        label = SCENARIO_LABELS.get(scenario.get("scenario"), scenario.get("title") or "研究情景")
        lines.extend(
            [
                f"### {label}",
                "",
                f"{scenario['judgment']} {_citations(scenario.get('evidence_ids') or [])}".rstrip(),
                "",
                "成立条件：" + _join_phrases(scenario.get("conditions") or []),
                "",
                "失效条件：" + _join_phrases(scenario.get("invalidation") or []),
                "",
            ]
        )

    questions = packet.get("research_questions") or []
    lines.extend(["## 下一步调查", ""])
    if questions:
        lines.extend(f"- {item['question']}" for item in questions)
    else:
        lines.append("- 当前研究数据包未识别出新增的强制补证项。")

    blockers = packet["quality"].get("blockers") or []
    lines.extend(
        [
            "",
            "## 数据质量与隔离",
            "",
            f"- 隔离字段数量：{len(packet['quality'].get('quarantined_fields') or [])}",
            "- 阻断项：" + ("；".join(BLOCKER_LABELS.get(item, item) for item in blockers) if blockers else "无"),
            f"- 引用覆盖率：{citation_display}",
            "",
            "本报告仅用于本地研究辅助，不执行交易，不构成投资建议或目标价判断。",
        ]
    )
    return "\n".join(lines) + "\n"


def validate_stock_research_report(
    report: str,
    packet: dict[str, Any],
    gate: dict[str, Any],
) -> dict[str, Any]:
    errors = []
    usable = set(packet["quality"].get("usable_evidence_ids") or [])
    cited = set(CITATION_PATTERN.findall(report))
    unknown = sorted(cited - usable)
    if unknown:
        errors.append({"code": "unknown_report_citation", "evidence_ids": unknown})

    for claim in gate.get("approved_claims") or []:
        if claim["statement"] not in report:
            errors.append({"code": "approved_claim_missing", "claim_id": claim["claim_id"]})
        missing_citations = [
            evidence_id
            for evidence_id in claim.get("evidence_ids") or []
            if f"[{evidence_id}]" not in report
        ]
        if missing_citations:
            errors.append({
                "code": "approved_claim_citation_missing",
                "claim_id": claim["claim_id"],
                "evidence_ids": missing_citations,
            })
    for claim in gate.get("rejected_claims") or []:
        if claim.get("statement") and claim["statement"] in report:
            errors.append({"code": "rejected_claim_leaked", "claim_id": claim.get("claim_id")})

    for path in packet["quality"].get("quarantined_fields") or []:
        dataset_name, _, field_name = path.partition(".")
        field = (
            packet.get("datasets", {}).get(dataset_name, {}).get("fields", {}).get(field_name, {})
        )
        raw_value = field.get("raw_value")
        if isinstance(raw_value, (int, float)) and abs(raw_value) >= 1_000:
            token = str(raw_value)
            if token in report or f"{raw_value:,}" in report:
                errors.append({"code": "quarantined_value_leaked", "path": path})

    expected_status = f"研究状态：{STATUS_LABELS.get(gate['report_status'], gate['report_status'])}"
    if expected_status not in report:
        errors.append({"code": "report_status_mismatch", "expected": gate["report_status"]})
    return {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "cited_evidence_ids": sorted(cited),
    }
