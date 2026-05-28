#!/usr/bin/env python3
import argparse,json,sqlite3,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_agents import DB_PATH
from smr_real_source_monitor_schema import get_sample_sources
from smr_real_source_event_classifier import build_classifier_result
from smr_metadata_to_watchlist_event_adapter import build_adapted_events
from smr_wiki import now_ts
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def build(conn,ticker):
    sources=get_sample_sources(ticker); classified=build_classifier_result(sources,ticker)
    adapted=build_adapted_events(classified.get("real_source_event_classifier",{}).get("event_rows",[]),ticker)
    events=adapted.get("metadata_watchlist_events",{}).get("events",[])
    stypes={}; etypes={}
    for s in sources: t=s.get("source_type","unknown"); stypes[t]=stypes.get(t,0)+1
    for e in events: t=e.get("event_type","unknown"); etypes[t]=etypes.get(t,0)+1
    return {"generated_at":now_ts(),"summary":{"ticker":ticker,"sources_checked":len(sources),"sources_found":len(sources),"metadata_only_sources":len(sources),"watchlist_events_created":len(events),"events_refreshed":len(events),"pending_created":0,"paper_order_created":0,"real_trade_created":0},"source_type_breakdown":stypes,"event_type_breakdown":etypes}
def md(p):
    s=p.get("summary")or{}; l=[f"# Phase 49 Real Source Event Dashboard","","## Summary"]
    for k,v in s.items(): l.append(f"- {k}: {v}")
    return "\n".join(l).rstrip()+"\n"
def main():
    p=argparse.ArgumentParser(); p.add_argument("--db-path",default=str(DB_PATH)); p.add_argument("--json",action="store_true"); p.add_argument("--markdown",action="store_true"); a=p.parse_args()
    conn=sqlite3.connect(a.db_path)
    try: pl=build(conn,"300308.SZ")
    finally: conn.close()
    if a.markdown and not a.json: print(md(pl),end="")
    else: print(json.dumps(pl,ensure_ascii=False,indent=2,default=str))
    return 0
if __name__=="__main__": raise SystemExit(main())
