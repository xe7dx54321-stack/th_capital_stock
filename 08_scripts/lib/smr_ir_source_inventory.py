#!/usr/bin/env python3
"""Phase 27 company IR and industry source inventory helpers."""

from __future__ import annotations

from typing import Any

from smr_supplier_exposure_model import get_supplier_exposure_profile, normalize_ticker


SOURCE_TYPES = {
    "annual_report",
    "semiannual_report",
    "quarterly_report",
    "investor_relations_record",
    "investor_interaction",
    "earnings_briefing",
    "company_announcement",
    "company_ir_webpage",
    "news_with_company_quote",
    "industry_public_commentary",
    "unknown",
}

MOCK_IR_TEXTS = {
    "300394.SZ": [
        {
            "source_type": "investor_relations_record",
            "title": "天孚通信投资者关系活动记录表摘要",
            "published_at": "2026-05-01",
            "source_url": "mock://ir/300394/2026-05-01",
            "text": (
                "问：高速光器件需求和产能情况如何？\n"
                "答：公司将持续推进高速光器件相关产能建设，以满足客户需求增长。"
                "公司未披露具体客户 allocation，也未披露单一客户供应份额。\n"
                "问：产品结构是否变化？\n"
                "答：高速产品占比提升带动产品结构优化，但公司未披露具体 ASP 或单价。"
            ),
        },
        {
            "source_type": "company_announcement",
            "title": "天孚通信经营情况说明摘要",
            "published_at": "2026-04-20",
            "source_url": "mock://announcement/300394/2026-04-20",
            "text": "公司高速光器件和先进光学封装产品应用于数据中心等场景。相关客户名称和出货量未在公告中披露。",
        },
    ],
    "300308.SZ": [
        {
            "source_type": "investor_relations_record",
            "title": "中际旭创投资者交流纪要摘要",
            "published_at": "2026-05-02",
            "source_url": "mock://ir/300308/2026-05-02",
            "text": (
                "问：800G 光模块需求如何？\n"
                "答：AI 数据中心对 800G 光模块需求保持较好景气度，公司会根据客户需求安排产能。"
                "该表述不构成确认订单，公司未披露客户 allocation 或供应份额。\n"
                "问：价格情况？\n"
                "答：产品结构变化会影响收入结构，但未披露具体 ASP。"
            ),
        }
    ],
    "688041.SH": [
        {
            "source_type": "annual_report",
            "title": "海光信息年度报告管理层讨论摘要",
            "published_at": "2026-04-30",
            "source_url": "mock://annual_report/688041/2026",
            "text": "国产算力需求增长带动公司产品需求，但该材料不涉及光模块供应份额、ASP 或客户 allocation。",
        }
    ],
    "002230.SZ": [
        {
            "source_type": "news_with_company_quote",
            "title": "科大讯飞公开交流摘要",
            "published_at": "2026-05-03",
            "source_url": "mock://news_quote/002230/2026-05-03",
            "text": "公司表示大模型应用需求增长，但这属于应用层需求信号，不是 AI 光互连公司订单或光模块出货证据。",
        }
    ],
}

MOCK_INDUSTRY_SOURCES = [
    {
        "source_id": "industry_public_ai_optical_001",
        "source_type": "industry_public_commentary",
        "title": "AI 数据中心光互连公开行业评论摘要",
        "published_at": "2026-05-05",
        "source_url": "mock://industry/ai_optical_interconnect/2026-05-05",
        "text": "公开行业评论认为 2025-2026 年 AI 数据中心网络升级将继续拉动 800G 光模块需求增长，但该判断不是公司特定订单。",
        "status": "available",
        "allowed_usage": "semantic_extraction_candidate",
    }
]


def build_source_id(ticker: str, index: int, source_type: str) -> str:
    stem = normalize_ticker(ticker).replace(".", "_").lower()
    return f"ir_{stem}_{source_type}_{index:03d}"


def build_ir_source_inventory(ticker: str) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    profile = get_supplier_exposure_profile(ticker)
    rows = []
    for index, item in enumerate(MOCK_IR_TEXTS.get(ticker, []), start=1):
        source_type = item.get("source_type") if item.get("source_type") in SOURCE_TYPES else "unknown"
        source_url = item.get("source_url")
        rows.append(
            {
                "source_id": item.get("source_id") or build_source_id(ticker, index, source_type),
                "ticker": ticker,
                "company_name": profile.get("company_name"),
                "source_type": source_type,
                "title": item.get("title"),
                "published_at": item.get("published_at"),
                "source_url": source_url,
                "status": "available" if item.get("text") else "source_missing",
                "allowed_usage": "semantic_extraction_candidate" if source_url else "context_only",
                "text": item.get("text") or "",
            }
        )
    by_type: dict[str, int] = {}
    for row in rows:
        by_type[row["source_type"]] = by_type.get(row["source_type"], 0) + 1
    return {
        "ticker": ticker,
        "company_name": profile.get("company_name"),
        "source_inventory": {
            "sources_found": len(rows),
            "sources_by_type": by_type,
            "sources": rows,
            "source_missing": len(rows) == 0,
        },
    }
