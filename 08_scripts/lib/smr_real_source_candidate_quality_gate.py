#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

def gate_candidate(candidate):
    meta=candidate.get("source_id","").find("_")>0
    quality="passed"
    if meta: quality="downgraded"
    notes=[]
    if quality=="downgraded": notes.append("metadata_or_fixture_source_penalty")
    if candidate.get("confidence","medium")=="low": quality="downgraded"
    return {"candidate_id":candidate.get("candidate_id"),"quality_status":quality,"allowed_usage_after_gate":"research_tracking_support","promotion_safe":True,"usable_for_promotion":False,"gate_notes":notes}

def build_quality_gate_report(candidates,ticker=TARGET_REVIEW_TICKER):
    rows=[gate_candidate(c) for c in candidates]
    passed=sum(1 for r in rows if r["quality_status"]=="passed")
    downgraded=sum(1 for r in rows if r["quality_status"]=="downgraded")
    rejected=len(rows)-passed-downgraded
    return {"generated_at":now_ts(),"ticker":normalize_ticker(ticker),"candidate_quality_gate":{"candidates_checked":len(candidates),"passed":passed,"downgraded":downgraded,"rejected":rejected,"usable_for_promotion_true":0,"rows":rows},"safety":{"quality_gate_allows_promotion":False,"sensitive_variables_not_confirmed":True}}
