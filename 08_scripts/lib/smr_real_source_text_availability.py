#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

AVAILABILITY_STATUSES = {"text_available","metadata_summary_only","download_required","download_unavailable","unsupported_file_type","too_large","requires_manual_input","sample_fixture_only","unknown"}
IR_FIXTURE = "Q: 公司目前高端光模块产品占比如何？A: 公司800G及以上产品占比持续提升，预计将继续保持增长趋势。Q: 订单可见度如何？A: 目前订单可见度较好，海外客户需求稳定。"
ANNUAL_FIXTURE = "2025年年度报告：公司实现营业收入XX亿元，光模块业务收入占比超过90%，其中高端产品占比持续提升。"
QUARTERLY_FIXTURE = "2026年第一季度报告：公司营收保持增长，光模块出货量同比增长XX%。"
EARNINGS_FIXTURE = "2026年半年度业绩预告：预计净利润同比增长XX%-XX%。"
ANNOUNCE_FIXTURE = "关于公司日常经营合同的公告：近日公司与客户签订XX合同。"
SOURCE_TEXT_MAP = {"cninfo_investor_relations":(IR_FIXTURE,"text_available","fixture"),"cninfo_annual_report":(ANNUAL_FIXTURE,"text_available","fixture"),"cninfo_quarterly_report":(QUARTERLY_FIXTURE,"text_available","fixture"),"cninfo_earnings_preview":(EARNINGS_FIXTURE,"text_available","fixture"),"cninfo_announcement":(ANNOUNCE_FIXTURE,"text_available","fixture")}

def assess_sources(sources):
    rows=[]
    for s in sources:
        st=s.get("source_type","unknown"); f=SOURCE_TEXT_MAP.get(st,(st,"download_unavailable",""))
        text=f[0] if f[2] else ""; status=f[1] if f[2] else "download_unavailable"
        rows.append({"source_id":s.get("source_id"),"source_type":st,"source_title":s.get("source_title"),"text_status":status,"text_origin":f[2] or "unavailable","has_text":status=="text_available","text_chars":len(text),"raw_content_saved":False,"allowed_next_action":"extract_clean_text" if status=="text_available" else "skip_or_metadata_only"})
    return rows

def build_report(sources,ticker=TARGET_REVIEW_TICKER):
    rows=assess_sources(sources)
    c={k:sum(1 for r in rows if r["text_status"]==k) for k in AVAILABILITY_STATUSES}
    return {"generated_at":now_ts(),"ticker":normalize_ticker(ticker),"real_source_text_availability":{"sources_checked":len(rows),**c,"sample_fixture_available":True,"rows":rows,"pending_created":0,"paper_order_created":0,"real_trade_created":0},"safety":{"availability_creates_pending":False,"availability_creates_order":False}}
