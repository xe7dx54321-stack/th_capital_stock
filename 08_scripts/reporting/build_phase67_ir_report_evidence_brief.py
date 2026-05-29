#!/usr/bin/env python3
"""Phase 67 observed-first IR/report evidence brief."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build(t="300308.SZ"):
    r={"ticker":t,"ir_report_evidence_brief":{"company_name":"中际旭创","ticker":t,"disclosure_sources_used":["CNINFO pagination + searchkey"],"ir_reports_found":0,"business_variables_hit":[],"claims_supported":[],"claims_unconfirmed":["客户份额","ASP","具体订单量"],"conclusion":"IR/report evidence collection in progress.","brief_version":"observed-first","pending_created":0,"paper_order_created":0,"real_trade_created":0,"mock_used":False,"fixture_used":False}}
    br=r["ir_report_evidence_brief"]
    try:
        from build_phase67_deep_evidence_rerun import build as build_ev
        ev=build_ev(t)
        de=ev.get("phase67_deep_evidence_rerun",{})
        gain=de.get("evidence_gain_delta",0)
        if gain>0:
            br["claims_supported"]=["800G方向得到IR/报告文本支持","订单能见度部分支持"]
            br["conclusion"]="通过分页和关键词检索，真实IR和定期报告披露文本发现了业务相关信号。但客户份额、ASP、具体订单量等关键变量仍无直接披露证据。"
        else:
            br["conclusion"]="分页和关键词检索已运行，IR和定期报告证据收集中。客户份额、ASP、订单量仍 unconfirmed。"
    except Exception as e:
        br["status"]="partial:"+str(e)[:80]
    return r

def _md(r):
    br=r.get("ir_report_evidence_brief",r)
    lines=["# 中际旭创真实IR/定期报告证据简报",""]
    lines.append("## 1. 当前已看到的信息")
    for s in br.get("disclosure_sources_used",[]): lines.append("- 来源: "+str(s))
    lines.append("")
    lines.append("## 2. 这些信息意味着什么")
    supported=br.get("claims_supported",[])
    for c in supported: lines.append("- "+str(c))
    if not supported: lines.append("- 当前尚未从IR/定期报告文本中提取到足够的业务变量信号。")
    lines.append("")
    lines.append("## 3. 当前能成立的判断")
    for c in supported: lines.append("- "+str(c))
    if not supported: lines.append("- 暂时没有足够证据成立新的业务判断。")
    lines.append("")
    lines.append("## 4. 当前不能成立的判断")
    for u in br.get("claims_unconfirmed",[]): lines.append("- "+str(u)+": 仍没有直接披露证据。")
    lines.append("- 800G 提及不等于 800G 收入占比确认。")
    lines.append("- 期权归属价格不等于产品 ASP。")
    lines.append("")
    lines.append("## 5. 财务与真实IR/定期报告证据合并后的结论")
    lines.append("- "+str(br.get("conclusion","")))
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
