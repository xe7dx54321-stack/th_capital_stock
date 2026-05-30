#!/usr/bin/env python3
from typing import Any
from pathlib import Path
import sys
L = Path(__file__).resolve().parent
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_phase74_html_parser_utils import chinese_ratio

def classify_html_text(ticker: str, source_type: str, text: str, link_count: int = 0) -> dict[str, Any]:
    if not text or not text.strip():
        return {"ticker": ticker, "source_type": source_type, "quality_grade": "rejected", "reason": "empty_text", "allowed_usage": "none"}
    tl = len(text.strip())

    if source_type == "irm_html":
        if tl < 5: return {"ticker": ticker, "source_type": source_type, "quality_grade": "text_too_short", "allowed_usage": "none"}
        return {"ticker": ticker, "source_type": source_type, "quality_grade": "usable_irm_qa", "allowed_usage": "management_commentary"}

    if source_type in ("sse_html", "szse_html"):
        if link_count > 0: return {"ticker": ticker, "source_type": source_type, "quality_grade": "link_only_page", "allowed_usage": "none"}
        return {"ticker": ticker, "source_type": source_type, "quality_grade": "usable_sse_exchange_text", "allowed_usage": "exchange_text"}

    if tl < 20:
        return {"ticker": ticker, "source_type": source_type, "quality_grade": "text_too_short", "allowed_usage": "none"}

    cr = chinese_ratio(text)
    bp = sum(1 for m in ["copyright", "备案号", "免责声明", "disclaimer", "版权所有", "风险提示", "技术支持"] if m in text.lower())
    if bp >= 3 and tl < 1000: return {"ticker": ticker, "source_type": source_type, "quality_grade": "boilerplate_heavy", "allowed_usage": "company_context"}
    mk = sum(1 for m in ["领先", "卓越", "一流", "最佳", "首创", "唯一", "第一品牌", "行业龙头"] if m in text)
    if mk >= 5: return {"ticker": ticker, "source_type": source_type, "quality_grade": "marketing_only", "allowed_usage": "company_context"}
    if tl < 200 and cr < 0.05: return {"ticker": ticker, "source_type": source_type, "quality_grade": "metadata_only", "allowed_usage": "none"}
    return {"ticker": ticker, "source_type": source_type, "quality_grade": "usable_company_context", "allowed_usage": "company_context"}
