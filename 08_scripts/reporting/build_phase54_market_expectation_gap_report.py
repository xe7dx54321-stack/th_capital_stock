#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_market_expectation_gap_checker import build_gap_report
def build(conn,ticker): return build_gap_report(ticker)
def _md(p): g=p.get("market_expectation_gap",{}); return "# Market Expectation Gap\n- status: "+str(g.get("expectation_gap_status",""))+"\n- confidence: "+str(g.get("expectation_gap_confidence",""))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args=p.parse_args()
    r=build(None,args.ticker)
    if args.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
