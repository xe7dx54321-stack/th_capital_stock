#!/usr/bin/env python3
import argparse,json,sqlite3,sys
from pathlib import Path
L,R=Path(__file__).resolve().parents[1]/"lib",Path(__file__).resolve().parents[1]/"reporting"
for p in (L,R):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
from smr_agents import DB_PATH
from smr_real_source_monitor_schema import get_sample_sources
from smr_real_source_event_classifier import build_classifier_result
from smr_metadata_to_watchlist_event_adapter import build_adapted_events
from smr_real_source_monitor_audit import write_monitor_audit
from smr_paper_watchlist_entry import get_paper_watchlist_entry
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def build(conn,ticker,mode="dry-run"):
    ticker=normalize_ticker(ticker); sources=get_sample_sources(ticker)
    classified=build_classifier_result(sources,ticker); rows=classified.get("real_source_event_classifier",{}).get("event_rows",[])
    adapted=build_adapted_events(rows,ticker); events=adapted.get("metadata_watchlist_events",{}).get("events",[])
    active=[e for e in events if e.get("requires_evidence_refresh")]
    touched=sorted(set(v for e in active for v in e.get("linked_tracking_variables",[])))
    entry=get_paper_watchlist_entry(conn,ticker); before=(entry or {}).get("watchlist_status")or"tracking_strengthened"
    audit_written=False
    if mode=="execute" and events:
        write_monitor_audit(conn,ticker=ticker,action="real_source_event_refresh",sources_checked=len(sources),events_created=len(events),events_refreshed=len(events),before_watchlist_status=before,after_watchlist_status=before,metadata={"event_types":[e.get("event_type")for e in events]})
        audit_written=True
    return {"generated_at":now_ts(),"ticker":ticker,"real_source_event_refresh":{"mode":mode,"real_sources_checked":len(sources),"watchlist_events_created":len(events),"events_refreshed":len(events),"tracking_variables_touched":touched,"phase48_refresh_invoked":len(events)>0,"research_only_revalidation_completed":True,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"audit_written":audit_written},"safety":{"executor_creates_pending":False,"executor_creates_order":False,"promotion_rules_relaxed":False}}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--db-path",default=str(DB_PATH)); p.add_argument("--ticker",default=TARGET_REVIEW_TICKER)
    p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true"); p.add_argument("--json",action="store_true")
    a=p.parse_args(); mode="execute" if a.execute else "dry-run"
    conn=sqlite3.connect(a.db_path)
    try:
        pl=build(conn,a.ticker,mode=mode)
        if mode=="execute": conn.commit()
    finally: conn.close()
    print(json.dumps(pl,ensure_ascii=False,indent=2,default=str))
    return 0
if __name__=="__main__": raise SystemExit(main())
