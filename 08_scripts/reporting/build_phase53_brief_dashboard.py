#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_executive_brief_builder import build_executive
from smr_brief_forbidden_phrase_checker import build_report
from smr_brief_style_lint import build_lint
from smr_tracking_decision_classifier import build_decision
from smr_wiki import now_ts
def build(conn=None,ticker="300308.SZ"):
    eb=build_executive(ticker); fp=build_report({"executive":eb}, ticker)
    lint=build_lint(json.dumps(eb,ensure_ascii=False))
    td=build_decision(ticker)
    fpr=fp.get("forbidden_phrase_report",{}); lint_r=lint.get("brief_style_lint",{})
    return {"generated_at":now_ts(),"summary":{"ticker":ticker,"brief_type":"internal_watchlist_tracking_brief","tracking_decision":td.get("tracking_decision",{}).get("decision",""),"style_status":lint_r.get("style_status",""),"forbidden_phrase_violations":fpr.get("violations",0),"forbidden_phrase_warnings":fpr.get("warnings",0),"has_executive_brief":True,"has_analyst_detail":True,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args=p.parse_args()
    r=build()
    if args.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
