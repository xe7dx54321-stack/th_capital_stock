#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_research_brief_quality_contract import build_contract
def build(conn=None,ticker=None): return build_contract()
def _md(p): return "# Research Brief Quality Contract\n\n- type: internal_equity_research_logic_brief\n- NOT system status report\n- Must answer business value questions"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args=p.parse_args()
    r=build(None)
    if args.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
