#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_investment_thesis_quality_checker import build_report
from smr_investment_logic_brief_builder import ONE_LINE
def build(conn,ticker): return build_report(ONE_LINE,ticker)
def _md(p): q=p.get("investment_thesis_quality",{}); return "# Thesis Quality\n- status: "+str(q.get("overall_status",""))+"\n- has_value: "+str(q.get("checks",{}).get("has_core_value_thesis",""))

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
