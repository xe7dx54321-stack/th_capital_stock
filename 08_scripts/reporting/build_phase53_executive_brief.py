#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_executive_brief_builder import build_executive
def build(conn,ticker): return build_executive(ticker)
def _md(p):
    eb=p.get("executive_brief",{})
    lines=["# "+p["ticker"]+" 内部投研跟踪简报","","## 老板摘要","","结论："]
    for x in eb.get("conclusion",[]): lines.append("- "+x)
    lines.append(""); lines.append("变化：")
    for x in eb.get("changes",[]): lines.append("- "+x)
    lines.append(""); lines.append("支撑：")
    for x in eb.get("support",[]): lines.append("- "+x)
    lines.append(""); lines.append("卡点：")
    for x in eb.get("blockers",[]): lines.append("- "+x[:80])
    lines.append(""); lines.append("下一步：")
    for x in eb.get("next_steps",[]): lines.append("- "+x[:80])
    lines.append(""); lines.append("> "+eb.get("forbidden_note",""))
    return "\n".join(lines)

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
