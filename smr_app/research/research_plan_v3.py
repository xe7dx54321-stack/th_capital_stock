from __future__ import annotations

from typing import Any


SECTION_SPECS: tuple[dict[str, Any], ...] = (
    {"section_id": "investment_summary", "title": "投资摘要与核心判断", "required": True,
     "questions": ["公司最重要的经营变化是什么？", "当前判断的核心依据和边界是什么？"]},
    {"section_id": "company_business", "title": "公司画像与商业模式", "required": True,
     "questions": ["公司靠什么产品和客户赚钱？", "采购、生产、销售和研发模式如何影响竞争力？"]},
    {"section_id": "industry", "title": "行业阶段与需求驱动", "required": True,
     "questions": ["行业处于什么阶段？", "需求由哪些可验证变量驱动？"]},
    {"section_id": "products_moat", "title": "产品矩阵与核心竞争力", "required": True,
     "questions": ["核心产品的速率、技术路线和应用场景是什么？", "领先优势能否持续？"]},
    {"section_id": "operations", "title": "经营模式、客户与供应链", "required": False,
     "questions": ["客户认证、订单、产能和供应链约束如何影响交付？"]},
    {"section_id": "financials", "title": "财务深度分析", "required": True,
     "questions": ["收入、利润、现金流、回报率和资产负债如何变化？", "增长质量如何？"]},
    {"section_id": "peers", "title": "同行比较与竞争格局", "required": True,
     "questions": ["可比公司是谁？", "目标公司在产品、增长和市场表现上处于什么位置？"]},
    {"section_id": "growth", "title": "增长驱动与预测边界", "required": True,
     "questions": ["未来增长由哪些变量驱动？", "哪些前提尚未获得证据？"]},
    {"section_id": "valuation", "title": "估值分析", "required": True,
     "questions": ["当前可用估值口径是什么？", "数据失效时应停在哪个判断边界？"]},
    {"section_id": "catalysts", "title": "催化剂与时间表", "required": False,
     "questions": ["未来 3—12 个月有哪些可验证事件？"]},
    {"section_id": "risks", "title": "风险、反面证据与证伪条件", "required": True,
     "questions": ["核心论点会因什么失效？", "应监控哪些预警信号？"]},
    {"section_id": "scenarios", "title": "三种情景", "required": True,
     "questions": ["乐观、基准和谨慎情景各自需要什么条件？"]},
    {"section_id": "tracking", "title": "后续跟踪指标", "required": True,
     "questions": ["后续更新报告时最少要跟踪哪些量化和事件指标？"]},
    {"section_id": "conclusion", "title": "结论", "required": True,
     "questions": ["在证据边界内，当前最重要的研究结论是什么？"]},
    {"section_id": "evidence_index", "title": "证据索引", "required": True,
     "questions": ["正文使用了哪些正式材料和辅助材料？"]},
)


def build_stock_research_plan(ticker: str, market: str) -> dict[str, Any]:
    sections = []
    questions = []
    for section in SECTION_SPECS:
        item = {key: value for key, value in section.items() if key != "questions"}
        item["status"] = "planned"
        sections.append(item)
        for index, question in enumerate(section["questions"], start=1):
            questions.append({
                "question_id": f"{section['section_id']}_{index}",
                "section_id": section["section_id"],
                "question": question,
                "status": "open",
            })
    return {
        "plan_version": "3.0",
        "ticker": ticker,
        "market": market,
        "sections": sections,
        "questions": questions,
        "methodology": [
            "official_filing_first",
            "claim_level_citations",
            "deterministic_financial_calculations",
            "section_level_degradation",
            "counter_evidence_required",
        ],
    }
