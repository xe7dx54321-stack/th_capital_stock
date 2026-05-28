#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_brief_forbidden_phrase_checker import build_report
from smr_executive_brief_builder import build_executive
from smr_analyst_detail_brief_builder import build_analyst_detail
def build(conn,ticker):
    parts={"executive":build_executive(ticker),"analyst":build_analyst_detail(ticker)}
    return build_report(parts,ticker)
def _md(p): r=p.get('forbidden_phrase_report',{}); s='# Forbidden Phrase Report\n- status: '+str(r.get('style_status',''))+'\n- violations: '+str(r.get('violations',0))+'\n- warnings: '+str(r.get('warnings',0)); return s

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
