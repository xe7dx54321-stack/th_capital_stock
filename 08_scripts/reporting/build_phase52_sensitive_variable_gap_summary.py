#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_agents import DB_PATH
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build(conn,ticker):
    return {"ticker":ticker,"sensitive_variable_gap_summary":{"pending_blocking_gaps":[{"variable":"official_consensus","current_status":"unconfirmed","why_it_matters":"cannot benchmark expectation gap against authorized consensus","required_next_evidence":"authorized consensus source metadata"},{"variable":"supplier_share","current_status":"scenario_only","why_it_matters":"cannot translate end-demand signal into company-specific revenue sensitivity","required_next_evidence":"direct company/customer disclosure or clearly labeled scenario assumption"},{"variable":"customer_allocation","current_status":"proxy_only","why_it_matters":"cannot confirm customer-specific allocation or demand capture","required_next_evidence":"direct disclosure or customer-side public statement"},{"variable":"valuation_boundary","current_status":"scenario_bound","why_it_matters":"cannot anchor valuation range without authorized consensus","required_next_evidence":"authorized consensus or management guidance"},{"variable":"bear_case_residual_risk","current_status":"partially_mitigated","why_it_matters":"competition, price erosion, demand shift risks persist","required_next_evidence":"industry-level shipment or pricing benchmark"}],"pending_allowed":False}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args=p.parse_args()
    result=build(None,args.ticker)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
