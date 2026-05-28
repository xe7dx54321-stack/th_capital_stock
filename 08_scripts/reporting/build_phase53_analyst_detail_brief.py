#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_analyst_detail_brief_builder import build_analyst_detail
def build(conn,ticker): return build_analyst_detail(ticker)
def _md(p):
    ad=p.get("analyst_detail",{})
    lines=["## 研究员详情","","支撑变量："]
    for v in ad.get("supported_variables",[]): lines.append("- "+v["variable"]+": "+v["status"])
    lines.append(""); lines.append("未确认变量：")
    for v in ad.get("unconfirmed_variables",[]): lines.append("- "+v["variable"]+": "+v["status"])
    lines.append(""); lines.append("Review required：")
    for x in ad.get("review_required",[]): lines.append("- "+x)
    lines.append(""); lines.append("下一步事件：")
    for x in ad.get("next_events",[])[:5]: lines.append("- "+x[:80])
    lines.append(""); lines.append("边界：")
    for x in ad.get("boundary",[]): lines.append("- "+x)
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
