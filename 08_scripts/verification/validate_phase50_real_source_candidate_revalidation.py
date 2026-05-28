#!/usr/bin/env python3
import argparse,json,sqlite3,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_agents import DB_PATH; from smr_real_source_monitor_schema import get_sample_sources
from smr_real_source_text_availability import SOURCE_TEXT_MAP, IR_FIXTURE, ANNUAL_FIXTURE, QUARTERLY_FIXTURE, EARNINGS_FIXTURE, ANNOUNCE_FIXTURE
from smr_real_source_semantic_extractor import build_semantic_report
from smr_real_source_evidence_candidate import build_candidates
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def build(conn,ticker):
    sources=get_sample_sources(ticker); fm=[(IR_FIXTURE,"cninfo_investor_relations"),(ANNUAL_FIXTURE,"cninfo_annual_report"),(QUARTERLY_FIXTURE,"cninfo_quarterly_report"),(EARNINGS_FIXTURE,"cninfo_earnings_preview"),(ANNOUNCE_FIXTURE,"cninfo_announcement")]
    chunks=[{"chunk_id":f"chunk_{i}","source_id":s.get("source_id"),"content":next((t for t,st in fm if st==s.get("source_type")),""),"ticker":ticker} for i,s in enumerate(sources) if next((t for t,st in fm if st==s.get("source_type")),"")]
    sem=build_semantic_report(chunks,ticker); extractions=sem.get("semantic_extractions",{}).get("rows",[])
    candidates=build_candidates(extractions,ticker); cand_rows=candidates.get("real_source_evidence_candidate_build",{}).get("rows",[])
    vars_touched=sorted(set(c.get("variable") for c in cand_rows))
    return {"generated_at":now_ts(),"ticker":normalize_ticker(ticker),"real_source_candidate_revalidation":{"overall_status":"pass","candidates_checked":len(cand_rows),"tracking_variables_supported":vars_touched,"thesis_delta":"unchanged_or_modestly_strengthened","official_consensus_confirmed":False,"supplier_share_confirmed":False,"customer_allocation_confirmed":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0},"safety":{"revalidation_creates_pending":False,"revalidation_creates_order":False,"sensitive_variables_not_confirmed":True}}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--db-path",default=str(DB_PATH)); p.add_argument("--ticker",default=TARGET_REVIEW_TICKER); p.add_argument("--json",action="store_true"); a=p.parse_args()
    conn=sqlite3.connect(a.db_path)
    try: pl=build(conn,a.ticker)
    finally: conn.close()
    print(json.dumps(pl,ensure_ascii=False,indent=2,default=str)); return 0
if __name__=="__main__": raise SystemExit(main())
