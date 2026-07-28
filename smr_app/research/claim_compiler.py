from __future__ import annotations

import hashlib
import re
from typing import Any


FIELD_LABELS = {
    "revenue": "营业收入",
    "gross_profit": "毛利润",
    "operating_income": "营业利润",
    "net_income": "净利润",
    "operating_cash_flow": "经营现金流",
    "capex": "资本开支",
    "free_cash_flow": "自由现金流",
    "cash_and_equivalents": "现金及等价物",
    "total_debt": "总债务",
    "shareholders_equity": "股东权益",
    "eps_basic": "基本每股收益",
    "eps_diluted": "稀释每股收益",
    "gross_margin": "毛利率",
    "operating_margin": "营业利润率",
    "net_margin": "净利率",
    "roe": "净资产收益率",
    "roic": "投入资本回报率",
}
VALUATION_LABELS = {
    "current_price": "当前价格",
    "market_cap": "总市值",
    "pe_ttm": "滚动市盈率",
    "ps_ttm": "滚动市销率",
    "pb": "市净率",
    "ev_ebitda_ttm": "企业价值倍数",
}
REPORTABLE_FUNDAMENTAL_FIELDS = {
    "revenue", "operating_income", "net_income", "operating_cash_flow",
    "gross_margin", "operating_margin", "net_margin", "roe",
}
SOURCE_LABELS = {
    "financial_statement_chunk": "巨潮资讯定期报告",
    "cninfo_announcement": "巨潮资讯公告",
    "official_filing": "公司正式披露",
    "hkex_announcement": "港交所公告",
    "sec_earnings_material": "美国证监会业绩材料",
    "sec_filing_document": "美国证监会申报文件",
    "sec_submissions_json": "美国证监会申报索引",
}
QUESTION_PATH_LABELS = {
    "fundamentals.revenue": "营业收入",
    "fundamentals.net_income": "净利润",
    "fundamentals.operating_cash_flow": "经营现金流",
    "fundamentals.gross_margin": "毛利率",
    "fundamentals.roe": "净资产收益率",
    "valuation": "估值数据",
    "risk.alerts": "风险事项",
}
FORBIDDEN_CONCLUSION_PATTERN = re.compile(
    r"(?:建议买入|建议卖出|强烈推荐|目标价|保证收益|必然上涨|必然下跌|"
    r"target\s+price|guaranteed\s+return|strong\s+buy)",
    re.IGNORECASE,
)


def _claim_id(ticker: str, category: str, source_paths: list[str], statement: str) -> str:
    payload = "|".join([ticker, category, *source_paths, statement])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"claim_{digest}"


def _format_value(value: float, unit: str) -> str:
    if unit == "ratio":
        return f"{value * 100:.2f}%"
    if unit.endswith("/share"):
        return f"{value:,.4g} {unit}"
    if unit in {"CNY", "HKD", "USD"}:
        labels = {"CNY": "人民币", "HKD": "港元", "USD": "美元"}
        absolute = abs(value)
        if absolute >= 1e8:
            return f"{value / 1e8:,.2f} 亿{labels[unit]}"
        if absolute >= 1e4:
            return f"{value / 1e4:,.2f} 万{labels[unit]}"
        return f"{value:,.2f} {labels[unit]}"
    return f"{value:,.4g} {unit}"


def _period_prefix(period: Any) -> str:
    value = str(period or "未记录").strip()
    if re.search(r"(?:Q[1-4]|FY|年度|半年)", value, re.IGNORECASE):
        return f"报告期 {value}"
    return f"数据口径日期 {value[:10]}"


def _make_claim(
    packet: dict[str, Any],
    *,
    category: str,
    statement: str,
    evidence_ids: list[str],
    source_paths: list[str],
    limitations: list[str] | None = None,
) -> dict[str, Any] | None:
    usable = set(packet["quality"].get("usable_evidence_ids") or [])
    citations = list(dict.fromkeys(value for value in evidence_ids if value in usable))
    if not citations or FORBIDDEN_CONCLUSION_PATTERN.search(statement):
        return None
    ticker = packet["ticker"]
    return {
        "claim_id": _claim_id(ticker, category, source_paths, statement),
        "category": category,
        "claim_type": category,
        "statement": " ".join(statement.split())[:800],
        "text": " ".join(statement.split())[:800],
        "evidence_ids": citations[:8],
        "source_paths": source_paths,
        "requires_evidence": True,
        "limitations": list(limitations or []),
    }


def _fundamental_claims(packet: dict[str, Any]) -> list[dict[str, Any]]:
    fundamentals = packet["datasets"]["fundamentals"]
    claims = []
    for name, field in (fundamentals.get("fields") or {}).items():
        if name not in REPORTABLE_FUNDAMENTAL_FIELDS:
            continue
        if field.get("status") != "valid" or field.get("value") is None:
            continue
        label = FIELD_LABELS.get(name, name)
        path = f"fundamentals.{name}"
        period = field.get("period") or fundamentals.get("period")
        fact = _make_claim(
            packet,
            category="fact",
            statement=f"{_period_prefix(period)}，{label}为 {_format_value(field['value'], field['unit'])}。",
            evidence_ids=field.get("evidence_ids") or [],
            source_paths=[path],
            limitations=["该数值仅对应所列报告期。"],
        )
        if fact:
            claims.append(fact)

        comparison = field.get("comparison") or {}
        if comparison.get("change_rate") is not None:
            if name in {"gross_margin", "operating_margin", "net_margin", "roe", "roic"}:
                absolute_change = comparison.get("absolute_change")
                if absolute_change is None:
                    absolute_change = field["value"] - comparison["previous_value"]
                direction = "上升" if absolute_change >= 0 else "下降"
                comparison_text = (
                    f"{label}相较 {comparison['previous_period']} "
                    f"{direction} {abs(absolute_change) * 100:.2f} 个百分点。"
                )
                limitation = "比例指标变化按本期与比较期的百分点差确定性计算。"
            else:
                direction = "增长" if comparison["change_rate"] >= 0 else "下降"
                comparison_text = (
                    f"{label}相较 {comparison['previous_period']} "
                    f"{direction} {abs(comparison['change_rate']) * 100:.2f}%。"
                )
                limitation = "变化率由同一字段的本期值与比较期值确定性计算。"
            change = _make_claim(
                packet,
                category="change",
                statement=comparison_text,
                evidence_ids=field.get("evidence_ids") or [],
                source_paths=[path],
                limitations=[limitation],
            )
            if change:
                claims.append(change)

        expectation = field.get("expectation") or {}
        if expectation.get("delta_rate") is not None:
            direction = "高于" if expectation["delta_rate"] >= 0 else "低于"
            expectation_claim = _make_claim(
                packet,
                category="expectation_gap",
                statement=f"{label}较已记录预期值{direction} {abs(expectation['delta_rate']) * 100:.2f}%。",
                evidence_ids=field.get("evidence_ids") or [],
                source_paths=[path],
                limitations=["仅比较 Packet 中显式记录的预期值，不代表市场一致预期。"],
            )
            if expectation_claim:
                claims.append(expectation_claim)
    return claims


def _evidence_claims(packet: dict[str, Any]) -> list[dict[str, Any]]:
    claims = []
    seen_summaries = set()
    for item in packet["datasets"]["evidence"].get("items") or []:
        if not item.get("usable_for_core_claim") or not item.get("text_excerpt"):
            continue
        category = "source_material"
        date = item.get("published_at") or "日期未记录"
        title = " ".join(str((item.get("metadata") or {}).get("title") or "").split())[:160]
        source_key = str(item.get("source_key") or item.get("source_type") or "来源材料")
        source_label = SOURCE_LABELS.get(source_key, source_key)
        display_date = str(date)[:10]
        if title:
            statement = f"证据包已收录{source_label}《{title}》（数据库记录日期：{display_date}）。"
        else:
            excerpt = " ".join(str(item.get("text_excerpt") or "").split())
            statement = (
                f"{display_date}，{source_label}记录：{excerpt[:220]}"
                if len(excerpt) <= 220
                else f"{display_date}，{source_label}的原始材料已纳入证据包，正文需通过原始链接复核。"
            )
        summary_key = (category, statement)
        if summary_key in seen_summaries:
            continue
        seen_summaries.add(summary_key)
        claim = _make_claim(
            packet,
            category=category,
            statement=statement,
            evidence_ids=[item.get("evidence_id")],
            source_paths=[f"evidence.{item.get('evidence_id')}"],
            limitations=["该陈述复述来源材料，不扩展解释其未披露内容。"],
        )
        if claim:
            claims.append(claim)
    return claims[:5]


def _valuation_claims(packet: dict[str, Any]) -> list[dict[str, Any]]:
    valuation = packet["datasets"]["valuation"]
    as_of = valuation.get("as_of")
    claims = []
    for name, field in (valuation.get("fields") or {}).items():
        if field.get("status") != "valid" or field.get("value") is None:
            continue
        label = VALUATION_LABELS.get(name, name)
        unit = field.get("unit") or ""
        suffix = " 倍" if unit == "multiple" else ""
        claim = _make_claim(
            packet,
            category="valuation",
            statement=f"截至 {as_of}，{label}为 {field['value']:,.4g}{suffix}。",
            evidence_ids=field.get("evidence_ids") or [],
            source_paths=[f"valuation.{name}"],
            limitations=["该字段仅作为时点事实，不据此推导高估、低估或目标价。"],
        )
        if claim:
            claims.append(claim)
    return claims


def _risk_claims(packet: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    claims = []
    questions = []
    for alert in packet["datasets"]["risk"].get("alerts") or []:
        evidence_ids = list(alert.get("evidence_ids") or [])
        claim = _make_claim(
            packet,
            category="risk",
            statement=f"风险记录：{' '.join(str(alert.get('message') or '').split())[:500]}",
            evidence_ids=evidence_ids,
            source_paths=[f"risk.alerts.{alert.get('alert_id') or 'unknown'}"],
            limitations=["风险记录不等同于风险已经发生。"],
        )
        if claim:
            claims.append(claim)
        elif alert.get("message") and not questions:
            questions.append({
                "path": "risk.alerts",
                "question": "存在未附原始证据的风险记录；补齐来源后再判断其对公司基本面的影响。",
                "reason": "risk_alert_without_usable_evidence",
            })
    return claims, questions


def _research_questions(packet: dict[str, Any]) -> list[dict[str, Any]]:
    questions = []
    for gap in packet.get("evidence_gaps") or []:
        path = gap.get("path") or "unknown"
        label = QUESTION_PATH_LABELS.get(path, "对应字段")
        questions.append(
            {
                "path": path,
                "question": f"补充并核验{label}的报告期、单位和原始证据。",
                "reason": ",".join(gap.get("reasons") or []) or gap.get("status") or "missing",
            }
        )
    return questions


def _scenarios(packet: dict[str, Any], claims: list[dict[str, Any]], supported: bool) -> list[dict[str, Any]]:
    evidence_ids = list(dict.fromkeys(
        evidence_id for claim in claims for evidence_id in claim.get("evidence_ids") or []
    ))[:8]
    if not supported:
        return [
            {
                "scenario": name,
                "title": title,
                "judgment": judgment,
                "conditions": conditions,
                "signposts": signposts,
                "invalidation": invalidation,
                "evidence_ids": [],
            }
            for name, title, judgment, conditions, signposts, invalidation in (
                (
                    "bull",
                    "乐观情景",
                    "暂不判断上行空间；只有正式数据补齐且核心经营指标改善，才进入乐观情景评估。",
                    ["补齐报告期明确的核心财务数据。", "经营与现金流指标出现同向改善。"],
                    ["下一期正式财报。", "公司正式经营披露。"],
                    ["补证后指标未改善。", "新增证据与改善假设相冲突。"],
                ),
                (
                    "base",
                    "基准情景",
                    "在证据补齐前维持观察，不把已收录材料外推为经营趋势。",
                    ["现有正式材料持续有效。", "后续数据未出现显著方向变化。"],
                    ["关键字段完成来源闭环。", "数据新鲜度恢复。"],
                    ["正式披露修正现有事实。", "数据质量继续恶化。"],
                ),
                (
                    "bear",
                    "谨慎情景",
                    "若补证后确认经营、现金流或风险指标恶化，再进入谨慎情景评估。",
                    ["核心指标出现可验证的反向变化。", "重大风险获得一手证据确认。"],
                    ["下一期正式财报。", "监管或公司风险披露。"],
                    ["风险未被正式证据确认。", "核心指标恢复改善。"],
                ),
            )
        ]
    scenario_specs = (
        (
            "bull",
            "乐观情景",
            "已验证的经营事实继续改善，且后续披露未出现相反证据。",
            ["核心经营指标延续改善。", "经营现金流与利润方向一致。"],
            ["下一报告期核心指标恶化。", "出现可验证的重大反向证据。"],
        ),
        (
            "base",
            "基准情景",
            "当前已批准事实继续成立，但不外推至尚未披露的期间。",
            ["下一报告期结果大体维持当前方向。", "数据质量和证据覆盖保持稳定。"],
            ["核心事实被正式披露修正。", "关键数据源失效或过期。"],
        ),
        (
            "bear",
            "谨慎情景",
            "后续正式证据显示核心经营指标或现金转化出现反向变化。",
            ["利润与现金流背离扩大。", "经证据确认的风险事件影响经营。"],
            ["反向变化未被后续正式披露确认。", "核心指标重新改善。"],
        ),
    )
    return [
        {
            "scenario": name,
            "title": title,
            "judgment": judgment,
            "conditions": conditions,
            "signposts": conditions,
            "invalidation": invalidation,
            "evidence_ids": evidence_ids,
        }
        for name, title, judgment, conditions, invalidation in scenario_specs
    ]


def compile_stock_claims(packet: dict[str, Any]) -> dict[str, Any]:
    if packet.get("schema_version") != "2.0":
        raise ValueError("Claim Compiler only accepts Research Packet schema_version=2.0")
    risk_claims, risk_questions = _risk_claims(packet)
    claims = [
        *_evidence_claims(packet),
        *_fundamental_claims(packet),
        *_valuation_claims(packet),
        *risk_claims,
    ]
    claims = list({claim["claim_id"]: claim for claim in claims}.values())
    has_core_fact = any(
        claim["category"] in {"fact", "change", "expectation_gap"}
        and any(path.startswith("fundamentals.") for path in claim["source_paths"])
        for claim in claims
    )
    supported = packet["quality"].get("readiness") == "research_ready" and has_core_fact
    return {
        "claims": claims,
        "scenarios": _scenarios(packet, claims, supported),
        "research_questions": [*_research_questions(packet), *risk_questions],
        "conclusion_status": "supported" if supported else "cannot_conclude",
    }


def validate_model_rewrites(
    packet: dict[str, Any],
    approved_claims: list[dict[str, Any]],
    rewrites: list[dict[str, Any]],
) -> dict[str, Any]:
    originals = {claim["claim_id"]: claim for claim in approved_claims}
    usable = set(packet["quality"].get("usable_evidence_ids") or [])
    accepted = []
    rejected = []
    for rewrite in rewrites:
        claim_id = str(rewrite.get("claim_id") or "")
        original = originals.get(claim_id)
        reasons = []
        if not original:
            reasons.append("unknown_claim_id")
        statement = " ".join(str(rewrite.get("statement") or "").split())
        evidence_ids = list(dict.fromkeys(rewrite.get("evidence_ids") or []))
        if FORBIDDEN_CONCLUSION_PATTERN.search(statement):
            reasons.append("forbidden_conclusion")
        if original and evidence_ids != original.get("evidence_ids"):
            reasons.append("citation_set_changed")
        if any(evidence_id not in usable for evidence_id in evidence_ids):
            reasons.append("unknown_evidence_id")
        if not statement:
            reasons.append("empty_statement")
        if reasons:
            rejected.append({"claim_id": claim_id, "reasons": list(dict.fromkeys(reasons))})
            continue
        accepted.append({**original, "statement": statement, "text": statement})
    return {"accepted_claims": accepted, "rejected_rewrites": rejected}
