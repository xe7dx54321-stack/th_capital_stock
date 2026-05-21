#!/usr/bin/env python3
"""Helpers for parsing and auditing SMR investment report candidates."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from smr_paths import normalize_project_path

REQUIRED_DASHBOARD_KEYS = {
    "action",
    "action_detail",
    "confidence",
    "portfolio_action_plan",
    "kill_triggers",
    "follow_up_tasks",
    "evidence_gap_tasks",
}

SOURCE_DISCIPLINE_TERMS = {
    "customer_capex": {
        "report_patterns": [
            "云厂商",
            "资本开支",
            "capex",
            "capital expenditures",
            "AI infrastructure",
            "AWS",
            "GCP",
            "Azure",
            "微软",
            "谷歌",
            "亚马逊",
            "Microsoft",
            "Alphabet",
            "Amazon",
            "Meta",
            "Meta Platforms",
        ],
        "evidence_patterns": [
            "云厂商",
            "资本开支",
            "capex",
            "capital expenditures",
            "AI infrastructure",
            "AWS",
            "GCP",
            "Azure",
            "微软",
            "谷歌",
            "亚马逊",
            "Microsoft",
            "Alphabet",
            "Amazon",
            "Meta",
            "Meta Platforms",
        ],
        "label": "云厂商资本开支 / 客户 capex",
    },
    "orders_visibility": {
        "report_patterns": ["订单能见度", "订单", "出货", "出货占比"],
        "evidence_patterns": ["订单能见度", "订单", "出货", "出货占比"],
        "label": "订单 / 出货 / 能见度",
    },
    "margin": {
        "report_patterns": ["毛利率", "利润率", "费用率", "良率"],
        "evidence_patterns": ["毛利率", "利润率", "费用率", "良率"],
        "label": "毛利率 / 利润率 / 良率",
    },
    "competition": {
        "report_patterns": ["竞争格局", "价格战", "华为", "光迅科技", "扩产"],
        "evidence_patterns": ["竞争格局", "价格战", "华为", "光迅科技", "扩产"],
        "label": "竞争格局 / 扩产 / 价格战",
    },
    "valuation_target": {
        "report_patterns": ["目标价", "估值", "PE", "PEG", "市盈率"],
        "evidence_patterns": ["目标价", "估值", "PE", "PEG", "市盈率", "pe_multiple"],
        "label": "估值 / 目标价",
    },
}

HARD_EVIDENCE_TASK_TEMPLATES = {
    "customer_capex": {
        "priority": "P0",
        "source_priority": [
            "official_customer_filings",
            "earnings_call_transcripts",
            "customer_capex_guidance",
            "company_ir_or_exchange_qa",
            "industry_data",
            "sell_side_cross_check",
        ],
        "accepted_evidence": [
            "Microsoft / Alphabet / Amazon / Meta 等客户最新 capex 实际值或指引",
            "客户管理层关于 AI 基建、数据中心、GPU/网络投入的原话",
            "公司或供应链关于订单、出货、客户结构的可追溯锚点",
        ],
        "query_templates": [
            "Microsoft latest earnings call capex AI infrastructure datacenter",
            "Alphabet latest earnings call capital expenditures AI infrastructure",
            "Amazon latest earnings call AWS capital expenditures AI datacenter",
            "Meta latest earnings call capex AI infrastructure datacenter",
        ],
        "research_question": "云厂商 AI capex 是否足以支撑本次调入腿的需求持续性假设？",
        "thesis_effect": "若客户 capex 上修且 AI 基建投入延续，可提高需求持续性与收入弹性置信度；若 capex 放缓、订单延后或客户切换供应商，调入腿需要降置信、降低仓位或推迟执行。",
    },
    "orders_visibility": {
        "priority": "P0",
        "source_priority": [
            "company_ir_or_exchange_qa",
            "earnings_call_transcripts",
            "order_backlog_disclosure",
            "shipment_mix_data",
            "supply_chain_channel_check",
            "sell_side_cross_check",
        ],
        "accepted_evidence": [
            "订单、在手订单、出货结构、客户集中度或产品 ramp 的公司口径",
            "多来源一致的产能利用率、排产、交付周期或客户拉货证据",
            "能解释未来 1-3 个季度收入能见度的时间锚点",
        ],
        "query_templates": [
            "{add_name} 订单 能见度 出货 800G 1.6T 投资者关系",
            "{add_name} 调研纪要 订单 出货 客户 产能",
        ],
        "research_question": "订单、出货和客户拉货节奏是否能支撑未来几个季度的收入超预期？",
        "thesis_effect": "若订单能见度强，可支持执行与加仓；若订单只来自单一来源或无法验证，结论降为素材型假设，执行应更偏试单。",
    },
    "margin": {
        "priority": "P1",
        "source_priority": [
            "financial_statements",
            "gross_margin_bridge",
            "management_commentary",
            "peer_margin_data",
            "pricing_or_asp_data",
            "sell_side_cross_check",
        ],
        "accepted_evidence": [
            "毛利率、经营利润率、产品结构或费用率的季度变化",
            "良率、成本、ASP、规模效应或产品 mix 的管理层解释",
            "可比公司利润率和价格压力对照",
        ],
        "query_templates": [
            "{add_name} 毛利率 良率 ASP 费用率 业绩说明会",
            "{add_name} gross margin product mix yield ASP",
        ],
        "research_question": "利润率扩张是否有财报和经营变量支持，还是只来自乐观模型假设？",
        "thesis_effect": "若毛利率改善有产品 mix/良率/ASP 锚点，可支持盈利弹性；若毛利率承压，应下调估值或降低仓位上限。",
    },
    "competition": {
        "priority": "P1",
        "source_priority": [
            "competitor_filings",
            "competitor_product_roadmap",
            "capacity_expansion_data",
            "pricing_news",
            "customer_dual_sourcing_evidence",
            "sell_side_cross_check",
        ],
        "accepted_evidence": [
            "主要竞争对手扩产、产品路线、价格策略或客户突破",
            "客户双供、份额变化、价格战或技术迭代证据",
            "公司相对竞争优势或劣势的可核验事实",
        ],
        "query_templates": [
            "{add_name} 竞争格局 价格战 扩产 800G 1.6T",
            "{add_name} competitor capacity pricing market share optical module",
        ],
        "research_question": "竞争格局是否会削弱本次调入腿的份额、价格或利润率假设？",
        "thesis_effect": "若竞争压力低于市场担忧，可支持估值重估；若价格战或客户份额切换加剧，应降低目标区间并设置更紧退出条件。",
    },
    "valuation_target": {
        "priority": "P1",
        "source_priority": [
            "multi_broker_models",
            "consensus_database",
            "peer_multiple_history",
            "scenario_model",
            "downside_case",
        ],
        "accepted_evidence": [
            "至少两家以上模型的收入、利润、EPS、估值倍数和目标价分歧",
            "基础/乐观/悲观情景下的核心假设和隐含空间",
            "历史和同业估值区间，尤其是下行风险区间",
        ],
        "query_templates": [
            "{add_name} EPS 目标价 PE 估值 分歧 研报",
            "{remove_name} EPS 目标价 PE 估值 分歧 研报",
        ],
        "research_question": "当前价格是否已经 price in 乐观预期，调仓后的风险收益比是否仍然成立？",
        "thesis_effect": "若上行空间来自未被充分定价的业绩差异，可支持调仓；若估值已经反映乐观情景，执行应缩小仓位并等待更好价格。",
    },
}


def load_text_rel_path(rel_path: str | None) -> str:
    path = normalize_project_path(rel_path)
    if path is None or not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def model_output_body(text: str | None) -> str:
    raw = str(text or "").strip()
    marker = "## Model Output"
    if marker in raw:
        return raw.split(marker, 1)[1].strip()
    return raw


def parse_json_object(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def first_balanced_json_object(text: str) -> str | None:
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escape_next = False
    for index, char in enumerate(text[start:], start=start):
        if in_string:
            if escape_next:
                escape_next = False
            elif char == "\\":
                escape_next = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def extract_dashboard_summary_json(report_text: str | None) -> dict[str, Any] | None:
    body = model_output_body(report_text)
    match = re.search(
        r"(?im)^##+\s*(?:\d+[.)、]?\s*)?(dashboard[_\s-]*summary[_\s-]*json)\s*$",
        body,
    )
    if not match:
        return None
    section = body[match.end() :]

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", section, flags=re.S | re.I)
    if fenced:
        parsed = parse_json_object(fenced.group(1))
        if parsed is not None:
            return normalize_dashboard_summary(parsed)

    candidate = first_balanced_json_object(section)
    if not candidate:
        return None
    return normalize_dashboard_summary(parse_json_object(candidate))


def normalize_dashboard_summary(summary: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(summary, dict):
        return None
    normalized = dict(summary)
    action_text = str(normalized.get("action") or "")
    if action_text:
        match = re.search(
            r"调入\s*(?P<in_name>.+?)\s*[（(](?P<in_ticker>[^)）]+)[)）]\s*/\s*调出\s*(?P<out_name>.+?)\s*[（(](?P<out_ticker>[^)）]+)[)）]",
            action_text,
        )
        if match:
            normalized.setdefault("in_name", match.group("in_name").strip())
            normalized.setdefault("in_ticker", match.group("in_ticker").strip())
            normalized.setdefault("out_name", match.group("out_name").strip())
            normalized.setdefault("out_ticker", match.group("out_ticker").strip())
    if not normalized.get("action_detail") and normalized.get("action_summary"):
        normalized["action_detail"] = normalized.get("action_summary")
    if not normalized.get("action_detail"):
        in_name = normalized.get("in_name") or normalized.get("add_name") or normalized.get("in_ticker") or "-"
        in_ticker = normalized.get("in_ticker") or normalized.get("add_ticker") or "-"
        out_name = normalized.get("out_name") or normalized.get("remove_name") or normalized.get("out_ticker") or "-"
        out_ticker = normalized.get("out_ticker") or normalized.get("remove_ticker") or "-"
        initial_action = ((normalized.get("portfolio_action_plan") or {}).get("initial_action") or {})
        buy_amount = ((initial_action.get("buy") or {}).get("amount_cny")) if isinstance(initial_action, dict) else None
        sell_amount = ((initial_action.get("sell") or {}).get("amount_cny")) if isinstance(initial_action, dict) else None
        amount_bits = []
        if buy_amount not in (None, ""):
            amount_bits.append(f"调入候选金额 {buy_amount}")
        if sell_amount not in (None, ""):
            amount_bits.append(f"调出候选金额 {sell_amount}")
        amount_text = "；".join(amount_bits)
        if action_text:
            normalized["action_detail"] = (
                f"内部研究候选：{action_text}"
                + (f"；{amount_text}" if amount_text else "")
                + "。所有动作需人工复核后才可进入正式执行。"
            )
        else:
            normalized["action_detail"] = (
                f"内部研究候选：调入 {in_name}({in_ticker}) / 调出 {out_name}({out_ticker})"
                + (f"；{amount_text}" if amount_text else "")
                + "。所有动作需人工复核后才可进入正式执行。"
            )
    if not normalized.get("follow_up_tasks") and normalized.get("next_review_date"):
        normalized["follow_up_tasks"] = [str(normalized.get("next_review_date"))]
    if not normalized.get("follow_up_tasks") and isinstance(normalized.get("evidence_gap_tasks"), list):
        followups = []
        for task in normalized.get("evidence_gap_tasks") or []:
            if not isinstance(task, dict):
                continue
            followups.append(
                {
                    "priority": task.get("priority") or "P1",
                    "task": task.get("research_question") or task.get("variable_label") or task.get("variable_id") or "补齐关键变量证据",
                    "frequency": "下一轮研究补证",
                }
            )
            if len(followups) >= 6:
                break
        if followups:
            normalized["follow_up_tasks"] = followups
    return normalized


def dashboard_summary_quality(summary: dict[str, Any] | None) -> dict[str, Any]:
    summary = summary or {}
    missing = sorted(key for key in REQUIRED_DASHBOARD_KEYS if key not in summary)
    action_plan = summary.get("portfolio_action_plan")
    kill_triggers = summary.get("kill_triggers")
    follow_up_tasks = summary.get("follow_up_tasks")
    evidence_gap_tasks = summary.get("evidence_gap_tasks")
    return {
        "valid": not missing
        and isinstance(action_plan, dict)
        and isinstance(kill_triggers, list)
        and isinstance(evidence_gap_tasks, list),
        "missing_keys": missing,
        "has_action_plan": isinstance(action_plan, dict) and bool(action_plan),
        "kill_trigger_count": len(kill_triggers) if isinstance(kill_triggers, list) else 0,
        "follow_up_task_count": len(follow_up_tasks) if isinstance(follow_up_tasks, list) else 0,
        "evidence_gap_task_count": len(evidence_gap_tasks) if isinstance(evidence_gap_tasks, list) else 0,
    }


def contains_any(text: str, patterns: list[str]) -> bool:
    lower = text.lower()
    return any(str(pattern).lower() in lower for pattern in patterns)


def source_discipline_audit(report_text: str | None, evidence_text: str | None) -> dict[str, Any]:
    report_body = model_output_body(report_text)
    evidence_body = str(evidence_text or "")
    findings = []
    for term_id, rule in SOURCE_DISCIPLINE_TERMS.items():
        report_hits = [pattern for pattern in rule["report_patterns"] if contains_any(report_body, [pattern])]
        if not report_hits:
            continue
        evidence_has_anchor = contains_any(evidence_body, rule["evidence_patterns"])
        if evidence_has_anchor:
            continue
        findings.append(
            {
                "term_id": term_id,
                "label": rule["label"],
                "severity": "needs_source",
                "report_hits": report_hits,
                "message": f"报告使用了“{rule['label']}”相关判断，但 evidence pack 中没有直接证据锚点；应标为待补证据或补抓来源。",
            }
        )

    missing_source_notes = []
    if "待补证据" not in report_body and findings:
        missing_source_notes.append("报告有来源缺口，但没有显式使用“待补证据”提示。")
    if "候选" not in report_body:
        missing_source_notes.append("报告未明确标记候选层边界。")

    return {
        "status": "needs_review" if findings or missing_source_notes else "pass",
        "finding_count": len(findings),
        "findings": findings,
        "missing_source_notes": missing_source_notes,
    }


def _listify(value: Any) -> list[Any]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_evidence_gap_task(task: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = {
        "add_name": "-",
        "add_code": "-",
        "remove_name": "-",
        "remove_code": "-",
        **(context or {}),
    }
    variable_id = str(task.get("variable_id") or task.get("term_id") or "unknown").strip() or "unknown"
    variable_label = (
        task.get("variable_label")
        or task.get("label")
        or (SOURCE_DISCIPLINE_TERMS.get(variable_id) or {}).get("label")
        or variable_id
    )
    priority = str(task.get("priority") or "P1").strip() or "P1"
    source_priority = [str(item) for item in _listify(task.get("source_priority")) if item not in (None, "")]
    accepted_evidence = [str(item) for item in _listify(task.get("accepted_evidence")) if item not in (None, "")]
    query_templates = []
    for item in _listify(task.get("query_templates")):
        if item in (None, ""):
            continue
        try:
            query_templates.append(str(item).format(**context))
        except KeyError:
            query_templates.append(str(item))
    return {
        "variable_id": variable_id,
        "variable_label": str(variable_label),
        "priority": priority,
        "research_question": str(task.get("research_question") or f"补齐“{variable_label}”的一手或硬数据证据。"),
        "source_priority": source_priority,
        "accepted_evidence": accepted_evidence,
        "query_templates": query_templates,
        "thesis_effect": str(task.get("thesis_effect") or "补证结果将用于调整置信度、仓位上限、执行时点或退出条件。"),
        "gap_reason": str(task.get("gap_reason") or task.get("message") or ""),
        "status": str(task.get("status") or "open"),
    }


def task_from_source_finding(finding: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    term_id = finding.get("term_id") or "unknown"
    template = HARD_EVIDENCE_TASK_TEMPLATES.get(term_id, {})
    task = {
        **template,
        "variable_id": term_id,
        "variable_label": finding.get("label") or (SOURCE_DISCIPLINE_TERMS.get(term_id) or {}).get("label") or term_id,
        "gap_reason": finding.get("message") or "",
    }
    return normalize_evidence_gap_task(task, context)


def evidence_gap_tasks_from_report(
    dashboard_summary: dict[str, Any] | None,
    source_audit: dict[str, Any] | None,
    context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    context = context or {}
    tasks: list[dict[str, Any]] = []
    seen: set[str] = set()

    summary_tasks = (dashboard_summary or {}).get("evidence_gap_tasks") or []
    if isinstance(summary_tasks, list):
        for raw_task in summary_tasks:
            if not isinstance(raw_task, dict):
                continue
            task = normalize_evidence_gap_task(raw_task, context)
            key = task.get("variable_id") or task.get("variable_label")
            if key in seen:
                continue
            seen.add(key)
            tasks.append(task)

    for finding in (source_audit or {}).get("findings") or []:
        if not isinstance(finding, dict):
            continue
        task = task_from_source_finding(finding, context)
        key = task.get("variable_id") or task.get("variable_label")
        if key in seen:
            continue
        seen.add(key)
        tasks.append(task)

    return tasks


def parse_report_dashboard_payload(report_rel_path: str | None, evidence_rel_path: str | None = None) -> dict[str, Any]:
    report_text = load_text_rel_path(report_rel_path)
    evidence_text = load_text_rel_path(evidence_rel_path)
    dashboard_summary = extract_dashboard_summary_json(report_text)
    source_audit = source_discipline_audit(report_text, evidence_text)
    return {
        "dashboard_summary": dashboard_summary,
        "dashboard_summary_quality": dashboard_summary_quality(dashboard_summary),
        "source_discipline_audit": source_audit,
        "evidence_gap_tasks": evidence_gap_tasks_from_report(dashboard_summary, source_audit),
    }
