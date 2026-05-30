#!/usr/bin/env python3
"""Phase 72: Fallback text quality classifier."""
from typing import Any

def classify_fallback_text(text: str, source_type: str, text_length: int) -> dict[str, Any]:
    """Classify fallback text quality."""
    if not text or text_length < 50:
        return {"quality_grade": "rejected", "reason": "text_too_short", "allowed_usage": "none"}

    text_lower = text.lower()
    if source_type == "irm":
        return {"quality_grade": "usable_irm_qa", "allowed_usage": "management_commentary",
                "limitation": "互动问答只能作为管理层表述，不确认客户份额或订单量。"}

    # Check for boilerplate
    boilerplate_signals = ["免责声明", "风险提示", "版权所有", "copyright", "disclaimer"]
    bp_count = sum(1 for s in boilerplate_signals if s in text_lower)
    bp_ratio = bp_count / max(text_length, 1)

    if "业绩预告" in text or "年度报告" in text or "季度报告" in text or "announcement" in text_lower:
        return {"quality_grade": "usable_exchange_text", "allowed_usage": "financial_report_context_or_business_context"}
    elif "投资者关系" in text or "ir" in text_lower or "investor" in text_lower:
        return {"quality_grade": "usable_company_context", "allowed_usage": "company_context"}
    elif text_length > 500:
        return {"quality_grade": "usable_known_url_text", "allowed_usage": "business_context"}
    elif bp_ratio > 0.1:
        return {"quality_grade": "boilerplate_heavy", "allowed_usage": "degraded_context"}
    else:
        return {"quality_grade": "metadata_only", "allowed_usage": "not_evidence", "reason": "insufficient_business_content"}

def build_text_quality_report(fallback_texts: list = None) -> dict[str, Any]:
    if fallback_texts is None:
        fallback_texts = []
    rows = []
    for t in fallback_texts:
        q = classify_fallback_text(t.get("text", ""), t.get("source_type", ""), t.get("text_length", 0))
        rows.append({"ticker": t.get("ticker", ""), "source_type": t.get("source_type", ""), **q})

    usable = sum(1 for r in rows if r["quality_grade"].startswith("usable"))
    metadata = sum(1 for r in rows if r["quality_grade"] == "metadata_only")
    rejected = len(rows) - usable - metadata
    return {"phase72_fallback_text_quality": {"texts_checked": len(rows), "texts_usable": usable, "metadata_only": metadata, "rejected": rejected, "rows": rows, "mock_used": False, "fixture_used": False}}
