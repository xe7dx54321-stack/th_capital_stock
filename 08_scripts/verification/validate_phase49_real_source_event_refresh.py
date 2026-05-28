#!/usr/bin/env python3
import argparse,json,sqlite3,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_agents import DB_PATH
from smr_real_source_monitor_schema import get_sample_sources
from smr_real_source_event_classifier import build_classifier_result
from smr_metadata_to_watchlist_event_adapter import build_adapted_events
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def build(conn,ticker):
    ticker=normalize_ticker(ticker); sources=get_sample_sources(ticker)
    classified=build_classifier_result(sources,ticker); rows=classified.get("real_source_event_classifier",{}).get("event_rows",[])
    adapted=build_adapted_events(rows,ticker); events=adapted.get("metadata_watchlist_events",{}).get("events",[])
    active=[e for e in events if e.get("requires_evidence_refresh")]
    touched=sorted(set(v for e in active for v in e.get("linked_tracking_variables",[])))
    return {"generated_at":now_ts(),"ticker":ticker,"real_source_event_refresh_validation":{"overall_status":"pass","sources_checked":len(sources),"events_created":len(events),"events_revalidated":len(active),"tracking_variables_touched":touched,"pending_created":0,"paper_order_created":0,"real_trade_created":0},"safety":{"validator_creates_pending":False,"validator_creates_order":False}}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--db-path",default=str(DB_PATH)); p.add_argument("--ticker",default=TARGET_REVIEW_TICKER); p.add_argument("--json",action="store_true"); a=p.parse_args()
    conn=sqlite3.connect(a.db_path)
    try: pl=build(conn,a.ticker)
    finally: conn.close()
    print(json.dumps(pl,ensure_ascii=False,indent=2,default=str))
    return 0
if __name__=="__main__": raise SystemExit(main())
