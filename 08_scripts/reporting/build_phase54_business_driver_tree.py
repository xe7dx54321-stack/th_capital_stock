#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_business_driver_tree import build_driver_tree
def build(conn,ticker): return build_driver_tree(ticker)
def _md(p): t=p.get("business_driver_tree",{}); lines=["# Business Driver Tree","","Root: "+str(t.get("root_driver","")),"","Industry:"]; [lines.append("- "+d) for d in t.get("industry_drivers",[])]; lines.append(""); lines.append("Company:"); [lines.append("- "+d) for d in t.get("company_drivers",[])]; lines.append(""); lines.append("Financial:"); [lines.append("- "+d) for d in t.get("financial_outputs",[])]; return "\n".join(lines)

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
