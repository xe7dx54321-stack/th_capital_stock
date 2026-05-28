#!/usr/bin/env python3
import argparse,json,sqlite3,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_agents import DB_PATH; from smr_real_source_monitor_schema import get_sample_sources
from smr_real_source_text_availability import SOURCE_TEXT_MAP, IR_FIXTURE, ANNUAL_FIXTURE, QUARTERLY_FIXTURE, EARNINGS_FIXTURE, ANNOUNCE_FIXTURE
from smr_real_source_text_normalizer import build_normalization_report
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def build(conn,ticker):
    sources=get_sample_sources(ticker)
    texts=[{"source_id":s.get("source_id"),"source_type":s.get("source_type"),"content":next((t for k,(t,_,_) in [("cninfo_investor_relations",(IR_FIXTURE,"","")),("cninfo_annual_report",(ANNUAL_FIXTURE,"","")),("cninfo_quarterly_report",(QUARTERLY_FIXTURE,"","")),("cninfo_earnings_preview",(EARNINGS_FIXTURE,"","")),("cninfo_announcement",(ANNOUNCE_FIXTURE,"",""))] if k==s.get("source_type")),""), "ticker":ticker} for s in sources]
    return build_normalization_report(texts,ticker)
def md(p): r=p.get("text_normalization_report")or{}; return f"# Phase 50 Text Normalization\n\n- texts_checked: {r.get('texts_checked')}\n- normalized_texts: {r.get('normalized_texts')}\n"
def main():
    p=argparse.ArgumentParser(); p.add_argument("--db-path",default=str(DB_PATH)); p.add_argument("--ticker",default=TARGET_REVIEW_TICKER); p.add_argument("--json",action="store_true"); p.add_argument("--markdown",action="store_true"); a=p.parse_args()
    conn=sqlite3.connect(a.db_path)
    try: pl=build(conn,a.ticker)
    finally: conn.close()
    if a.markdown and not a.json: print(md(pl),end="")
    else: print(json.dumps(pl,ensure_ascii=False,indent=2,default=str))
    return 0
if __name__=="__main__": raise SystemExit(main())
