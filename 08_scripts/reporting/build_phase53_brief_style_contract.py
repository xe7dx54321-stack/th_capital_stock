#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_brief_style_contract import build_contract
def build(conn=None,ticker=None): return build_contract()
def _md(p): c=p.get("brief_style_contract",{}); return "# Brief Style Contract\n\n- type: "+str(c.get("brief_type",""))+"\n- not: sell_side_research_report"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args=p.parse_args()
    r=build()
    if args.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
