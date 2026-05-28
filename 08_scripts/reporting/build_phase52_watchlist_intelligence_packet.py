#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_agents import DB_PATH
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_watchlist_intelligence_aggregator import aggregate_intelligence
from smr_human_readable_thesis_summary import build_thesis_summary
from smr_tracking_decision_classifier import build_decision
from build_phase52_tracking_support_evidence_summary import build as build_ts
from build_phase52_sensitive_variable_gap_summary import build as build_svg
from build_phase52_review_required_candidate_summary import build as build_rrc
from build_phase52_next_event_watchlist import build as build_new
from build_phase52_tracking_decision import build as build_td
def build(conn,ticker):
    agg=aggregate_intelligence(ticker)
    thesis=build_thesis_summary(ticker)
    ts_sum=build_ts(conn,ticker)
    svg=build_svg(conn,ticker)
    rrc=build_rrc(conn,ticker)
    new=build_new(conn,ticker)
    td=build_td(conn,ticker)
    return {"ticker":ticker,"watchlist_intelligence_packet":{"aggregator":agg.get("watchlist_intelligence_aggregator",{}),"human_thesis_summary":thesis.get("human_thesis_summary",{}),"tracking_support_evidence_summary":ts_sum.get("tracking_support_evidence_summary",{}),"sensitive_variable_gap_summary":svg.get("sensitive_variable_gap_summary",{}),"review_required_candidate_summary":rrc.get("review_required_candidate_summary",{}),"next_event_watchlist":new.get("next_event_watchlist",{}),"tracking_decision":td.get("tracking_decision",{}),"boundary":{"pending_created":0,"paper_order_created":0,"real_trade_created":0,"promotion_allowed_true":0}}}

def _md(p):
    a=p.get("watchlist_intelligence_packet",{}); h=a.get("human_thesis_summary",{}); td=a.get("tracking_decision",{})
    b=a.get("boundary",{})
    lines=[]
    lines.append("# Phase 52 Watchlist Tracking Intelligence: "+p["ticker"])
    lines.append("")
    lines.append("## One-Line Summary")
    lines.append(h.get("one_line_summary",""))
    lines.append("")
    lines.append("## Current Thesis Status")
    lines.append("- status: "+str(h.get("current_thesis_status","")))
    lines.append("- score: "+str(h.get("thesis_strength_score","")))
    lines.append("- delta: "+str(h.get("thesis_delta","")))
    lines.append("")
    lines.append("## Why Continue Tracking")
    for r in h.get("why_continue_tracking",[]): lines.append("- "+str(r))
    lines.append("")
    lines.append("## Why Not Pending")
    for r in h.get("why_not_pending",[]): lines.append("- "+str(r))
    lines.append("")
    lines.append("## Tracking Decision")
    lines.append("- decision: "+str(td.get("decision","")))
    lines.append("- confidence: "+str(td.get("decision_confidence","")))
    lines.append("")
    lines.append("## Why Not Order/Trade")
    lines.append("- pending: 0")
    lines.append("- paper_order: 0")
    lines.append("- real_trade: 0")
    lines.append("- promotion: 0")
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args=p.parse_args()
    result=build(None,args.ticker)
    if args.markdown: print(_md(result))
    else: print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
