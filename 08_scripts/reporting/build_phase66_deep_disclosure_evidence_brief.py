#!/usr/bin/env python3
"""Phase 66 observed-first deep disclosure evidence brief."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build(t="300308.SZ"):
    r={"ticker":t,"deep_disclosure_evidence_brief":{"company_name":"中际旭创","ticker":t,"disclosure_sources_used":[],"business_variables_hit":[],"claims_supported":[],"claims_unconfirmed":["客户份额","ASP","具体订单量"],"risk_signals":[],"conclusion":"Real disclosure evidence collection in progress.","brief_version":"observed-first","pending_created":0,"paper_order_created":0,"real_trade_created":0,"mock_used":False,"fixture_used":False}}
    br=r["deep_disclosure_evidence_brief"]
    try:
        from build_phase66_deep_evidence_claim_map import build as build_cm
        cm=build_cm(t)
        claims=cm.get("deep_evidence_claim_map",{})
        supported=[row.get("claim","") for row in claims.get("rows",[]) if row.get("claim_status")=="supported"]
        br["claims_supported"]=supported
        from build_phase66_business_keyword_hit_scan import build as build_kw
        kw=build_kw(t)
        kws=kw.get("business_keyword_hit_scan",{})
        hits=set()
        for row in kws.get("rows",[]):
            for g in row.get("keyword_groups_hit",[]): hits.add(g)
        br["business_variables_hit"]=list(hits)
        from build_phase66_deep_business_evidence_extraction import build as build_ev
        ev=build_ev(t)
        deep=ev.get("deep_business_evidence_extraction",{})
        if deep.get("evidence_created",0)>0:
            br["disclosure_sources_used"]=["CNINFO targeted disclosure harvest"]
            br["conclusion"]="真实披露文本中发现了业务相关信号，但客户份额、ASP、订单量等关键变量仍无直接披露证据支持。"
        else:
            br["conclusion"]="当前尚未提取足够的可用真实披露文本，证据收集仍在进行中。"
    except Exception as e:
        br["status"]="partial:"+str(e)[:80]
    return r

def _md(r):
    br=r.get("deep_disclosure_evidence_brief",r)
    lines=["# 中际旭创真实披露证据简报",""]
    lines.append("## 1. 当前已看到的信息")
    for s in br.get("disclosure_sources_used",[]):
        lines.append("- 来源: "+str(s))
    v=br.get("business_variables_hit",[])
    if v:
        lines.append("- 命中的业务变量: "+", ".join(v))
    else:
        lines.append("- 当前尚未从真实披露文本中提取到足够的业务变量信号。")
    lines.append("")
    lines.append("## 2. 这些信息意味着什么")
    supported=br.get("claims_supported",[])
    if supported:
        for c in supported:
            lines.append("- "+str(c).replace("_"," ")+" 方向得到真实披露文本支持。")
        lines.append("- 但所有这些支持都有明确局限：不能确认具体数量指标、份额或价格。")
    else:
        lines.append("- 当前没有足够真实披露文本支持特定业务判断。")
    lines.append("")
    lines.append("## 3. 当前能成立的判断")
    if supported:
        for c in supported:
            lines.append("- "+str(c).replace("_"," "))
    else:
        lines.append("- 暂时没有足够证据成立新的业务判断。")
    lines.append("")
    lines.append("## 4. 当前不能成立的判断")
    for u in br.get("claims_unconfirmed",[]):
        lines.append("- "+str(u)+": 仍没有直接披露证据。")
    lines.append("- 800G 提及不等于 800G 收入占比确认。")
    lines.append("- 1.6T 提及不等于 1.6T 大规模放量确认。")
    lines.append("- 客户需求强不等于客户份额提升确认。")
    lines.append("- 订单能见度好不等于具体订单金额或订单量确认。")
    lines.append("")
    lines.append("## 5. 财务与真实披露证据合并后的结论")
    lines.append("- "+str(br.get("conclusion","")))
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
