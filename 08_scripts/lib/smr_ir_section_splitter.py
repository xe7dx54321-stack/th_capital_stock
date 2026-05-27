#!/usr/bin/env python3
"""Split extracted IR text into prioritized semantic sections."""

from __future__ import annotations

import re
from typing import Any

from smr_document_text_extraction import normalize_whitespace


SECTION_TYPES = {
    "qa_section",
    "management_discussion",
    "business_overview",
    "capacity_expansion",
    "product_structure",
    "customer_market",
    "margin_price",
    "risk_factor",
    "financial_summary",
    "unknown",
}


SECTION_HINTS = [
    ("qa_section", ("问：", "答：", "问:", "答:", "投资者关系活动主要内容", "问答")),
    ("management_discussion", ("管理层讨论", "经营情况讨论", "管理层分析")),
    ("business_overview", ("主营业务", "业务概要", "主要业务")),
    ("capacity_expansion", ("产能", "扩产", "募投项目", "产能建设")),
    ("product_structure", ("产品结构", "研发", "产品升级", "800G", "1.6T")),
    ("customer_market", ("客户", "市场", "海外", "北美")),
    ("margin_price", ("毛利", "价格", "单价", "ASP")),
    ("risk_factor", ("风险因素", "不确定", "风险")),
    ("financial_summary", ("财务", "收入", "利润", "现金流")),
]


def classify_section(text: str, title: str | None = None) -> str:
    haystack = f"{title or ''}\n{text or ''}".lower()
    for section_type, terms in SECTION_HINTS:
        if any(term.lower() in haystack for term in terms):
            return section_type
    return "unknown"


def section_priority(section_type: str) -> str:
    if section_type in {"qa_section", "capacity_expansion", "product_structure", "customer_market", "margin_price"}:
        return "high"
    if section_type in {"management_discussion", "business_overview", "risk_factor"}:
        return "medium"
    return "low"


def split_ir_sections(source: dict[str, Any], *, max_section_chars: int = 5000) -> dict[str, Any]:
    text = normalize_whitespace(source.get("text"))
    if not text:
        return {"source_id": source.get("source_id"), "sections": []}
    blocks = [block.strip() for block in re.split(r"\n{2,}", text) if block.strip()]
    if not blocks:
        blocks = [text]
    sections = []
    buffer = ""
    current_title = str(source.get("title") or "unknown")
    for block in blocks:
        if buffer and len(buffer) + len(block) > max_section_chars:
            sections.append(_make_section(source, len(sections), buffer, current_title))
            buffer = block
        else:
            buffer = f"{buffer}\n\n{block}".strip()
    if buffer:
        sections.append(_make_section(source, len(sections), buffer, current_title))
    return {"source_id": source.get("source_id"), "sections": sections}


def _make_section(source: dict[str, Any], index: int, text: str, title: str) -> dict[str, Any]:
    section_type = classify_section(text, title)
    return {
        "section_id": f"section_{index + 1:03d}",
        "section_type": section_type,
        "title": title,
        "text": text,
        "char_count": len(text),
        "priority": section_priority(section_type),
        "source_id": source.get("source_id"),
    }
