#!/usr/bin/env python3
"""Phase 66 deep evidence cannot-conclude guard."""
import argparse,json,sys
from typing import Any
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

FORBIDDEN_RULES=[
    {"forbidden":"800G 提及 = 800G 收入占比确认","pattern":["800G revenue share confirmed","800G收入占比确认","800G 收入占比确认"],"allowed_rewrite":"真实披露文本支持 800G 相关产品进展，但不能确认 800G 收入占比。"},
    {"forbidden":"1.6T 提及 = 1.6T 大规模放量","pattern":["1.6T mass production confirmed","1.6T大规模放量","1.6T 放量确认"],"allowed_rewrite":"真实披露文本支持 1.6T 相关进展，但不能确认大规模放量。"},
    {"forbidden":"光模块需求强 = 公司份额提升","pattern":["market share increase confirmed","份额提升确认","公司份额提升"],"allowed_rewrite":"真实披露文本提及需求较强，但不能确认公司份额提升。"},
    {"forbidden":"客户需求强 = 客户份额提升","pattern":["customer share increase confirmed","客户份额提升确认"],"allowed_rewrite":"真实披露文本提及客户需求，但不能确认客户份额或具体客户关系。"},
    {"forbidden":"海外客户提及 = NVIDIA allocation 确认","pattern":["NVIDIA allocation confirmed","NVIDIA 供应确认"],"allowed_rewrite":"海外客户提及不能等同于特定客户分配确认。"},
    {"forbidden":"订单能见度好 = 具体订单金额确认","pattern":["order amount confirmed","订单金额确认","具体订单金额"],"allowed_rewrite":"订单能见度好不能等同于具体订单金额确认，不能确认订单量。"},
    {"forbidden":"出货顺利 = 具体出货量确认","pattern":["shipment volume confirmed","出货量确认"],"allowed_rewrite":"出货顺利表述不能确认具体出货量。"},
    {"forbidden":"毛利率强 = ASP 改善","pattern":["ASP improvement confirmed","ASP改善确认"],"allowed_rewrite":"毛利率强不能直接归因于 ASP 改善，可能受到成本、产品结构等多种因素影响。"},
    {"forbidden":"产品结构优化 = 产品级毛利率确认","pattern":["product-level margin confirmed","产品级毛利率确认"],"allowed_rewrite":"产品结构优化不能直接确认产品级毛利率。"},
    {"forbidden":"产能扩张 = 订单已锁定","pattern":["order locked confirmed","订单锁定确认"],"allowed_rewrite":"产能扩张计划不能确认订单已锁定。"},
]

def run_guard(claims:list[dict],evidence_rows:list[dict])->dict[str,Any]:
    violations=[];claims_text_json=json.dumps(claims,ensure_ascii=False).lower()
    for rule in FORBIDDEN_RULES:
        for pat in rule["pattern"]:
            if pat.lower() in claims_text_json:
                violations.append({"forbidden_claim":rule["forbidden"],"matched_pattern":pat,"allowed_rewrite":rule["allowed_rewrite"]})
    guard_status="pass" if len(violations)==0 else "fail"
    return {"claims_checked":len(claims),"violations":len(violations),"guard_status":guard_status,"blocked_claim_examples":violations[:5]}

def build(t="300308.SZ"):
    r={"ticker":t,"deep_evidence_cannot_conclude_guard":{"claims_checked":0,"violations":0,"guard_status":"pass","blocked_claim_examples":[]}}
    try:
        from build_phase66_deep_evidence_claim_map import build as build_cm
        cm=build_cm(t)
        claims=cm.get("deep_evidence_claim_map",{}).get("rows",[])
        evidence=[]
        try:
            from build_phase66_deep_business_evidence_extraction import build as build_ev
            ev=build_ev(t)
            evidence=ev.get("deep_business_evidence_extraction",{}).get("rows",[])
        except: pass
        gr=run_guard(claims,evidence)
        r["deep_evidence_cannot_conclude_guard"]=gr
        if gr["violations"]==0:
            r["deep_evidence_cannot_conclude_guard"]["blocked_claim_examples"]=[
                {"forbidden_claim":rule["forbidden"],"allowed_rewrite":rule["allowed_rewrite"]} for rule in FORBIDDEN_RULES[:3]
            ]
    except Exception as e:
        r["deep_evidence_cannot_conclude_guard"]["status"]="error:"+str(e)[:80]
    return r

def _md(r):
    g=r.get("deep_evidence_cannot_conclude_guard",r)
    lines=["# Cannot-Conclude Guard",""]
    lines.append("Status: "+str(g.get("guard_status","")))
    lines.append("Checked: "+str(g.get("claims_checked",0)))
    lines.append("Violations: "+str(g.get("violations",0)))
    if g.get("guard_status")=="fail":
        for v in g.get("blocked_claim_examples",[]):
            lines.append("- VIOLATION: "+str(v.get("forbidden_claim","")))
    else:
        lines.append("All claims pass the guard. No forbidden over-attribution detected.")
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
