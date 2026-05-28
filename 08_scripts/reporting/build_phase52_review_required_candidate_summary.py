#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_agents import DB_PATH
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_candidate_quality_gate_calibration import build_calibration
from smr_real_source_evidence_candidate import build_candidates
from smr_real_source_monitor_schema import get_sample_sources
from smr_real_source_semantic_extractor import build_semantic_report
from smr_real_source_text_availability import IR_FIXTURE, ANNUAL_FIXTURE, QUARTERLY_FIXTURE, EARNINGS_FIXTURE, ANNOUNCE_FIXTURE
def build(conn,ticker):
    sources=get_sample_sources(ticker)
    fm=[(IR_FIXTURE,"cninfo_investor_relations"),(ANNUAL_FIXTURE,"cninfo_annual_report"),(QUARTERLY_FIXTURE,"cninfo_quarterly_report"),(EARNINGS_FIXTURE,"cninfo_earnings_preview"),(ANNOUNCE_FIXTURE,"cninfo_announcement")]
    chunks=[{"chunk_id":f"chunk_{i}","source_id":s.get("source_id"),"content":next((t for t,st in fm if st==s.get("source_type")),""),"ticker":ticker} for i,s in enumerate(sources) if next((t for t,st in fm if st==s.get("source_type")),"")]
    sem=build_semantic_report(chunks,ticker); extractions=sem.get("semantic_extractions",{}).get("rows",[])
    cand=build_candidates(extractions,ticker); candidates=cand.get("real_source_evidence_candidate_build",{}).get("rows",[])
    cal=build_calibration(candidates,ticker); rows=cal["quality_gate_calibration"]["rows"]
    rr=[r for r in rows if r["quality_status_after"]=="review_required"]
    rr_rows=[{"candidate_id":r["candidate_id"],"variable":r.get("variable"),"review_reason":["sensitive_variable_guard","proxy_not_confirmed"],"allowed_review_actions":["keep_proxy_only","downgrade_usage","reject_candidate","request_better_source"],"forbidden_review_actions":["confirm_customer_allocation","confirm_supplier_share","confirm_official_consensus","create_pending","create_order","create_trade"]} for r in rr]
    return {"ticker":ticker,"review_required_candidate_summary":{"review_required_candidates":len(rr_rows),"sensitive_variable_items":len(rr_rows),"rows":rr_rows}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args=p.parse_args()
    result=build(None,args.ticker)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
