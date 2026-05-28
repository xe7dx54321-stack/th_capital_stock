#!/usr/bin/env python3
"""Phase 49 real source monitor schema."""

from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import generate_execution_id, now_ts

SOURCE_TYPES = {
    "cninfo_announcement", "cninfo_investor_relations",
    "cninfo_annual_report", "cninfo_semiannual_report",
    "cninfo_quarterly_report", "cninfo_earnings_preview",
    "cninfo_earnings_flash", "company_ir_record",
    "existing_source_inventory", "unknown",
}
SAMPLE_SOURCES_300308 = [
    {"source_type": "cninfo_investor_relations",
     "source_title": "投资者关系活动记录表",
     "source_date": "2026-05-20", "source_provider": "cninfo",
     "source_url": "https://www.cninfo.com.cn/new/disclosure/detail?stockCode=300308"},
    {"source_type": "cninfo_annual_report",
     "source_title": "2025年年度报告",
     "source_date": "2026-04-25", "source_provider": "cninfo",
     "source_url": "https://www.cninfo.com.cn/new/disclosure/detail?stockCode=300308&announcementId=annual2025"},
    {"source_type": "cninfo_quarterly_report",
     "source_title": "2026年第一季度报告",
     "source_date": "2026-04-25", "source_provider": "cninfo",
     "source_url": "https://www.cninfo.com.cn/new/disclosure/detail?stockCode=300308&announcementId=q12026"},
    {"source_type": "cninfo_earnings_preview",
     "source_title": "2026年半年度业绩预告",
     "source_date": "2026-05-15", "source_provider": "cninfo",
     "source_url": "https://www.cninfo.com.cn/new/disclosure/detail?stockCode=300308&announcementId=preview"},
    {"source_type": "cninfo_announcement",
     "source_title": "关于公司日常经营合同的公告",
     "source_date": "2026-05-10", "source_provider": "cninfo",
     "source_url": "https://www.cninfo.com.cn/new/disclosure/detail?stockCode=300308&announcementId=contract"},
]

def build_real_source_metadata(ticker=TARGET_REVIEW_TICKER, source_type="unknown", source_title="", source_date="", source_url="", source_provider="cninfo"):
    ticker = normalize_ticker(ticker)
    return {"ticker": ticker, "source_id": generate_execution_id(f"real_source_{ticker.split('.')[0]}_cninfo"),
            "source_type": source_type if source_type in SOURCE_TYPES else "unknown",
            "source_title": source_title, "source_date": source_date, "source_url": source_url,
            "source_provider": source_provider, "raw_content_saved": False, "metadata_only": True,
            "source_status": "metadata_discovered", "allowed_next_action": "classify_event_from_metadata",
            "forbidden_actions": ["create_pending","create_order","create_trade"],
            "pending_created": False, "paper_order_created": False, "real_trade_created": False}

def get_sample_sources(ticker=TARGET_REVIEW_TICKER):
    ticker = normalize_ticker(ticker)
    results = []
    for s in SAMPLE_SOURCES_300308:
        if ticker == "300308.SZ":
            results.append(build_real_source_metadata(ticker, s["source_type"], s["source_title"], s["source_date"], s["source_url"], s["source_provider"]))
    return results
