#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import generate_execution_id, now_ts

def build_candidate(extraction):
    return {"candidate_id":generate_execution_id(f"candidate_{normalize_ticker(extraction.get('ticker','300308.SZ')).split('.')[0]}_{extraction.get('variable','unknown')}"),"source_id":extraction.get("source_id"),"chunk_id":extraction.get("chunk_id"),"extraction_id":extraction.get("extraction_id"),"variable":extraction.get("variable"),"quoted_span":extraction.get("quoted_span",""),"confidence":extraction.get("confidence","medium"),"allowed_usage":"research_tracking_support","confirmation_status":"candidate_not_confirmed","usable_for_promotion":False}

def build_candidates(extractions,ticker=TARGET_REVIEW_TICKER,mode="dry-run"):
    candidates=[build_candidate(e) for e in extractions]
    return {"ticker":normalize_ticker(ticker),"real_source_evidence_candidate_build":{"mode":mode,"semantic_extractions_checked":len(extractions),"candidates_created":len(candidates),"candidates_written":len(candidates),"duplicates_skipped":0,"usable_for_promotion_true":0,"confirmed_variables_added":0,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"rows":candidates},"safety":{"candidates_not_confirmed":True,"no_promotion_allowed":True}}
