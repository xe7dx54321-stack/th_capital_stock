#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_financial_transmission_chain import build_transmission_chain
def build(conn,ticker): return build_transmission_chain(ticker)
def _md(p): tc=p.get("financial_transmission_chain",{}); lines=["# Financial Transmission Chain","","status: "+str(tc.get("overall_status",""))]; [lines.append("- "+c.get("business_driver","")+" -> "+c.get("financial_metric","")+" ("+c.get("current_evidence_status","")+")") for c in tc.get("chains",[])]; return "\n".join(lines)

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
