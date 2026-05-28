#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_brief_style_lint import build_lint
from smr_executive_brief_builder import build_executive
def build(conn,ticker):
    eb=build_executive(ticker)
    text=json.dumps(eb,ensure_ascii=False)
    return build_lint(text,True,True,True,True,True)
def _md(p): l=p.get('brief_style_lint',{}); s='# Style Lint\n- status: '+str(l.get('style_status',''))+'\n- passed: '+str(l.get('checks_passed',0)); return s

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
