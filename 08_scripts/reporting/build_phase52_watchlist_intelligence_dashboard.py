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
from smr_wiki import now_ts
def build(conn,ticker):
    agg=aggregate_intelligence(ticker); ai=agg.get("watchlist_intelligence_aggregator",{})
    ts=build_thesis_summary(ticker); h=ts.get("human_thesis_summary",{})
    td=build_decision(ticker)
    return {"generated_at":now_ts(),"summary":{"ticker":ticker,"watchlist_status":ai.get("current_watchlist_status",""),"tracking_decision":td.get("tracking_decision",{}).get("decision",""),"tracking_support_candidates":ai.get("tracking_support_candidates",0),"review_required_candidates":ai.get("review_required_candidates",0),"key_supported_variables":len(ai.get("key_supported_variables",[])),"key_unconfirmed_variables":len(ai.get("key_unconfirmed_variables",[])),"thesis_strength_score":ai.get("thesis_strength_score",0),"pending_created":0,"paper_order_created":0,"real_trade_created":0,"promotion_allowed_true":0}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args=p.parse_args()
    result=build(None,args.ticker)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
