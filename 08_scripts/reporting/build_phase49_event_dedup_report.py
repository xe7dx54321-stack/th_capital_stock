#!/usr/bin/env python3
import argparse,json,sqlite3,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_agents import DB_PATH
from smr_real_source_monitor_schema import get_sample_sources
from smr_real_source_event_classifier import build_classifier_result
from smr_metadata_to_watchlist_event_adapter import build_adapted_events
from smr_real_source_event_dedup import build_dedup_report
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def build(conn,ticker):
    sources=get_sample_sources(ticker); classified=build_classifier_result(sources,ticker)
    adapted=build_adapted_events(classified.get("real_source_event_classifier",{}).get("event_rows",[]),ticker)
    events=adapted.get("metadata_watchlist_events",{}).get("events",[])
    return build_dedup_report(events,ticker)
def md(p):
    d=p.get("event_dedup_report")or{}
    return f"# Phase 49 Event Dedup: {p.get('ticker')}\n\n- events_checked: {d.get('events_checked')}\n- unique_events: {d.get('unique_events')}\n- duplicates_skipped: {d.get('duplicates_skipped')}\n"
def main():
    p=argparse.ArgumentParser(); p.add_argument("--db-path",default=str(DB_PATH)); p.add_argument("--ticker",default=TARGET_REVIEW_TICKER); p.add_argument("--json",action="store_true"); p.add_argument("--markdown",action="store_true"); a=p.parse_args()
    conn=sqlite3.connect(a.db_path)
    try: pl=build(conn,a.ticker)
    finally: conn.close()
    if a.markdown and not a.json: print(md(pl),end="")
    else: print(json.dumps(pl,ensure_ascii=False,indent=2,default=str))
    return 0
if __name__=="__main__": raise SystemExit(main())
