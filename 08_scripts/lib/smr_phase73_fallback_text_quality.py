#!/usr/bin/env python3
"""Phase 73: Fallback text quality classifier."""
from typing import Any

def classify_fallback_text(ticker: str, source_type: str, text: str) -> dict[str, Any]:
    if not text or not text.strip():
        return {"ticker": ticker, "source_type": source_type, "quality_grade": "rejected", "reason": "empty_text", "allowed_usage": "none"}
    tl = len(text.strip())
    if source_type == "irm":
        if tl < 5:
            return {"ticker": ticker, "source_type": source_type, "quality_grade": "text_too_short", "reason": "text_length_below_5", "allowed_usage": "none"}
        return {"ticker": ticker, "source_type": source_type, "quality_grade": "usable_irm_qa", "allowed_usage": "management_commentary"}
    if tl < 20:
        return {"ticker": ticker, "source_type": source_type, "quality_grade": "text_too_short", "reason": "text_length_below_20", "allowed_usage": "none"}
    tlw = text.lower()
    if tl < 200 and sum(1 for m in ["announcement", "title:", "code:"] if m in tlw) >= 2:
        return {"ticker": ticker, "source_type": source_type, "quality_grade": "metadata_only", "allowed_usage": "none"}
    if source_type in ("sse", "szse"):
        return {"ticker": ticker, "source_type": source_type, "quality_grade": "usable_exchange_text", "allowed_usage": "exchange_text"}
    if source_type in ("company_ir_page", "known_url", "seeded_url"):
        bp = sum(1 for m in ["免责声明", "disclaimer", "copyright", "版权所有", "风险提示"] if m in tlw)
        if bp >= 3 and tl < 1000:
            return {"ticker": ticker, "source_type": source_type, "quality_grade": "boilerplate_heavy", "allowed_usage": "company_context"}
        mk = sum(1 for m in ["领先", "卓越", "一流", "最佳", "首创", "唯一", "第一品牌", "行业龙头"] if m in text)
        if mk >= 5:
            return {"ticker": ticker, "source_type": source_type, "quality_grade": "marketing_only", "allowed_usage": "company_context"}
        return {"ticker": ticker, "source_type": source_type, "quality_grade": "usable_company_context", "allowed_usage": "company_context"}
    return {"ticker": ticker, "source_type": source_type, "quality_grade": "usable_company_context", "allowed_usage": "company_context"}
