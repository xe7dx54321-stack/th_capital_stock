#!/usr/bin/env python3
"""Phase 67b observed-first IR/report evidence brief."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def build(t="300308.SZ"):
    r={"ticker":t,"phase67b_ir_report_evidence_brief":{"company_name":"中际旭创","ticker":t,"high_value_pdfs_downloaded":0,"pdfs_with_text":0,"business_variables_hit":[],"claims_supported":[],"claims_unconfirmed":["客户份额","ASP","具体订单量"],"conclusion":"Evidence collection in progress.","pending_created":0,"paper_order_created":0,"real_trade_created":0,"mock_used":False,"fixture_used":False}}
    br=r["phase67b_ir_report_evidence_brief"]
    try:
        from build_phase67b_high_value_pdf_text_extraction_report import build as build_tx
        tx=build_tx(t,skip=True);br["pdfs_with_text"]=tx.get("high_value_pdf_text_extraction",{}).get("pdf_text_ok",0)
        from build_phase67b_evidence_claim_map import build as build_cm
        cm=build_cm(t);gain=cm.get("phase67b_evidence_claim_map",{}).get("evidence_gain_delta",0)
        if gain>0: br["conclusion"]="通过高价值PDF下载和深度证据抽取，IR和定期报告文本发现了业务证据增量。但客户份额、ASP、订单量仍 unconfirmed。"
        else: br["conclusion"]="高价值PDF已执行下载和文本提取。当前未产生新的claim strengthening，证据收集继续。"
    except Exception as e: br["status"]="partial:"+str(e)[:80]
    return r
def _md(r):
    br=r.get("phase67b_ir_report_evidence_brief",r)
    lines=["# 中际旭创高价值IR/定期报告证据简报","","## 1. 当前已看到的信息"]
    lines.append("- 已下载高价值PDF并提取正文: "+str(br.get("pdfs_with_text",0))+" 份")
    lines.append("## 2. 这些信息意味着什么")
    supported=br.get("claims_supported",[])
    for c in supported: lines.append("- "+str(c))
    if not supported: lines.append("- 当前尚未从高价值PDF文本中提取到足够业务变量信号。")
    lines.append("## 3. 当前能成立的判断")
    for c in supported: lines.append("- "+str(c))
    if not supported: lines.append("- 暂时没有足够证据成立新的业务判断。")
    lines.append("## 4. 当前不能成立的判断")
    for u in br.get("claims_unconfirmed",[]): lines.append("- "+str(u)+": 仍没有直接披露证据。")
    lines.append("- 期权归属价格不等于产品 ASP。")
    lines.append("## 5. 财务与真实IR/定期报告证据合并后的结论")
    lines.append("- "+str(br.get("conclusion","")));return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
