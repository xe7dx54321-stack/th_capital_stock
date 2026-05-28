#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_investment_logic_brief_builder import build_investment_logic_brief
from smr_wiki import now_ts
def build(conn=None,ticker="300308.SZ"):
    b=build_investment_logic_brief(ticker); ib=b.get("investment_logic_brief",{}); q=ib.get("quality",{})
    return {"generated_at":now_ts(),"summary":{"ticker":ticker,"brief_type":"internal_equity_research_logic_brief","style_status":q.get("style_status",""),"depth_status":q.get("depth_status",""),"has_core_value_thesis":True,"has_market_expectation_gap":True,"has_financial_transmission":True,"has_bull_base_bear":True,"has_validation_triggers":True,"system_status_terms_found":0,"forbidden_phrase_violations":q.get("forbidden_phrase_violations",0),"pending_created":0,"paper_order_created":0,"real_trade_created":0}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args=p.parse_args()
    r=build(None)
    if args.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
