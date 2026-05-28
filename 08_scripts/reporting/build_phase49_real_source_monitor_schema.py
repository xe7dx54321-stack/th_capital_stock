#!/usr/bin/env python3
"""Build Phase 49 real source monitor schema."""
import argparse, json, sys
from pathlib import Path
LIB = Path(__file__).resolve().parents[1] / "lib"
if str(LIB) not in sys.path: sys.path.insert(0, str(LIB))
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
from smr_real_source_monitor_schema import get_sample_sources, SOURCE_TYPES
from smr_wiki import now_ts
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def build(ticker=TARGET_REVIEW_TICKER):
    samples = get_sample_sources(ticker)
    return {"generated_at":now_ts(),"ticker":ticker,"event_trigger_schema":{"supported_source_types":sorted(SOURCE_TYPES),"always_forbidden_actions":["create_pending","create_order","create_trade"],"sample_sources":samples},"safety":{"schema_defines_pending":False,"schema_defines_order":False}}
def md(p):
    s=p.get("event_trigger_schema")or{}; l=[f"# Phase 49 Real Source Monitor Schema: {p.get('ticker')}","","## Supported Source Types"]
    for t in s.get("supported_source_types")or[]: l.append(f"- {t}")
    l.extend(["","## Sample Sources"])
    for r in s.get("sample_sources")or[]: l.append(f"- {r.get('source_type')}: {r.get('source_title')}")
    return "\n".join(l).rstrip()+"\n"
def main():
    p=argparse.ArgumentParser(); p.add_argument("--db-path",default=""); p.add_argument("--ticker",default=TARGET_REVIEW_TICKER); p.add_argument("--json",action="store_true"); p.add_argument("--markdown",action="store_true"); a=p.parse_args()
    pl=build(a.ticker)
    if a.markdown and not a.json: print(md(pl),end="")
    else: print(json.dumps(pl,ensure_ascii=False,indent=2,default=str))
    return 0
if __name__=="__main__": raise SystemExit(main())
