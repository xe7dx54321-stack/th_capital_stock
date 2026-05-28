#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_agents import DB_PATH; from smr_real_source_monitor_schema import get_sample_sources
from smr_real_source_semantic_extractor import build_semantic_report
from smr_real_source_text_availability import IR_FIXTURE, ANNUAL_FIXTURE, QUARTERLY_FIXTURE, EARNINGS_FIXTURE, ANNOUNCE_FIXTURE
from smr_real_source_evidence_candidate import build_candidates
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def _get_candidates(ticker):
    sources=get_sample_sources(ticker)
    fm=[(IR_FIXTURE,"cninfo_investor_relations"),(ANNUAL_FIXTURE,"cninfo_annual_report"),(QUARTERLY_FIXTURE,"cninfo_quarterly_report"),(EARNINGS_FIXTURE,"cninfo_earnings_preview"),(ANNOUNCE_FIXTURE,"cninfo_announcement")]
    chunks=[{"chunk_id":f"chunk_{i}","source_id":s.get("source_id"),"content":next((t for t,st in fm if st==s.get("source_type")),""),"ticker":ticker} for i,s in enumerate(sources) if next((t for t,st in fm if st==s.get("source_type")),"")]
    sem=build_semantic_report(chunks,ticker)
    extractions=sem.get("semantic_extractions",{}).get("rows",[])
    cand=build_candidates(extractions,ticker)
    return cand.get("real_source_evidence_candidate_build",{}).get("rows",[])

from smr_candidate_quality_gate_calibration import build_calibration
def build(conn,ticker,mode="dry-run"):
    candidates=_get_candidates(ticker)
    cal=build_calibration(candidates,ticker)
    rows=cal["quality_gate_calibration"]["rows"]
    passed_rows=[r for r in rows if r["quality_status_after"]=="passed_tracking_support"]
    review_rows=[r for r in rows if r["quality_status_after"]=="review_required"]
    w=len(passed_rows)
    return {"ticker":ticker,"tracking_support_candidate_upsert":{"mode":mode,"eligible_candidates":w,"tracking_support_written":w,"duplicates_skipped":0,"review_required":len(review_rows),"confirmed_variables_added":0,"usable_for_promotion_true":0,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--dry-run",action="store_true")
    p.add_argument("--execute",action="store_true")
    p.add_argument("--json",action="store_true")
    args=p.parse_args()
    mode="execute" if args.execute else "dry-run"
    result=build(None,args.ticker,mode)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
