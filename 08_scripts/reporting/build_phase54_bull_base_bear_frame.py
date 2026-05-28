#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_bull_base_bear_frame import build_frame
def build(conn,ticker): return build_frame(ticker)
def _md(p): f=p.get("bull_base_bear_frame",{}); lines=["# Bull/Base/Bear Frame","","## Bull"]; [lines.append("- "+b) for b in f.get("bull_case",[])]; lines.append(""); lines.append("## Base"); [lines.append("- "+b) for b in f.get("base_case",[])]; lines.append(""); lines.append("## Bear"); [lines.append("- "+b) for b in f.get("bear_case",[])]; return "\n".join(lines)

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
