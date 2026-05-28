#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_agents import DB_PATH
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build(conn,ticker):
    return {"ticker":ticker,"next_event_watchlist":{"events_to_watch":[{"event_type":"new_investor_relations_record","priority":"high","why_it_matters":"may update product_mix/order_visibility/shipment tracking variables","expected_action":"event_driven_revalidation","forbidden_action":"create_order"},{"event_type":"quarterly_report","priority":"high","why_it_matters":"may update shipment/margin_signal/valuation_boundary","expected_action":"event_driven_revalidation","forbidden_action":"create_order"},{"event_type":"earnings_preview","priority":"medium","why_it_matters":"may provide margin signal and forward guidance","expected_action":"research_revalidation","forbidden_action":"create_order"},{"event_type":"authorized_consensus_source_update","priority":"high","why_it_matters":"may improve expectation gap benchmark quality","expected_action":"research_revalidation","forbidden_action":"auto_confirm_consensus"},{"event_type":"major_customer_or_order_announcement","priority":"medium","why_it_matters":"may update order_visibility/customer_allocation_proxy","expected_action":"event_driven_revalidation","forbidden_action":"create_order"},{"event_type":"bear_case_worsening_event","priority":"medium","why_it_matters":"may weaken thesis and trigger re-evaluation","expected_action":"bear_case_revalidation","forbidden_action":"create_order"}],"monitoring_mode":"watchlist_tracking_only"}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args=p.parse_args()
    result=build(None,args.ticker)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
