#!/usr/bin/env python3
"""Phase 49 real source event classifier."""

from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

IR_KEYWORDS = ["投资者关系活动记录表","调研","机构调研","电话会议","路演","线上交流会"]
REPORT_KEYWORDS = ["年度报告","半年度报告","季度报告","年报","半年报","季报"]
PREVIEW_KEYWORDS = ["业绩预告","业绩预增","业绩预减"]
FLASH_KEYWORDS = ["业绩快报"]
CONTRACT_KEYWORDS = ["合同","订单","项目","客户","中标"]
CLASSIFICATION_RULES = [
    (IR_KEYWORDS, "investor_relations_record", ["product_mix","order_visibility","shipment","ASP_price_proxy"], "medium"),
    (REPORT_KEYWORDS, "earnings_report", ["shipment","valuation_boundary","bear_case_residual_risk"], "high"),
    (PREVIEW_KEYWORDS, "earnings_preview", ["valuation_boundary","bear_case_residual_risk"], "high"),
    (FLASH_KEYWORDS, "earnings_flash", ["shipment","valuation_boundary"], "medium"),
    (CONTRACT_KEYWORDS, "major_announcement", ["order_visibility","customer_allocation_proxy"], "medium"),
]

def classify_source(source: dict[str, Any]) -> dict[str, Any]:
    title = source.get("source_title","")
    stype = source.get("source_type","")
    event_type="unknown"; variables=[]; strength="low"; confidence="low"
    for keywords, et, vars, strn in CLASSIFICATION_RULES:
        if any(kw in title for kw in keywords):
            event_type=et; variables=list(vars); strength=strn; confidence="medium"
            break
    if event_type=="unknown" and stype in {"cninfo_annual_report","cninfo_semiannual_report","cninfo_quarterly_report"}:
        event_type="earnings_report"; variables=["shipment","valuation_boundary","bear_case_residual_risk"]; strength="high"; confidence="medium"
    elif event_type=="unknown" and stype=="cninfo_investor_relations":
        event_type="investor_relations_record"; variables=["product_mix","order_visibility","shipment"]; strength="medium"; confidence="medium"
    elif event_type=="unknown" and stype=="cninfo_earnings_preview":
        event_type="earnings_preview"; variables=["valuation_boundary","bear_case_residual_risk"]; strength="high"; confidence="medium"
    return {"source_id": source.get("source_id"), "source_title": title, "source_type": stype,
            "event_type": event_type, "linked_tracking_variables": variables,
            "event_strength": strength, "requires_evidence_refresh": event_type != "unknown",
            "requires_revalidation": event_type != "unknown",
            "classification_confidence": confidence}

def build_classifier_result(sources: list[dict[str, Any]], ticker=TARGET_REVIEW_TICKER):
    rows = [classify_source(s) for s in sources]
    active = [r for r in rows if r["event_type"] != "unknown"]
    return {"generated_at": now_ts(), "ticker": normalize_ticker(ticker),
            "real_source_event_classifier": {
                "sources_checked": len(sources), "events_classified": len(active),
                "low_relevance_sources": len(rows) - len(active), "event_rows": rows,
                "pending_created": 0, "paper_order_created": 0},
            "safety": {"classifier_only_uses_metadata": True, "classifier_creates_pending": False,
                       "title_hit_is_not_text_evidence": True}}
