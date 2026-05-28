#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_investment_logic_brief_builder import build_investment_logic_brief
def build(conn,ticker): return build_investment_logic_brief(ticker)
def _md(p):
    b=p.get("investment_logic_brief",{})
    lines=["# 中际旭创内部投研简报","","## 1. 一句话结论","",b.get("one_line_conclusion",""),""]
    cj=b.get("core_value_judgment",{})
    lines.append("## 2. 核心价值判断")
    lines.append("- 价值来源: "+str(cj.get("value_source","")))
    lines.append("- 关键变量: "+", ".join(cj.get("key_variables",[])))
    lines.append("- 判断强度: "+str(cj.get("conviction","")))
    lines.append("")
    kbd=b.get("key_business_drivers",{})
    lines.append("## 3. 关键业务变量")
    lines.append("- 根驱动: "+str(kbd.get("root_driver","")))
    [lines.append("- 行业: "+d) for d in kbd.get("industry_drivers",[])]
    [lines.append("- 公司: "+d) for d in kbd.get("company_drivers",[])]
    lines.append("")
    ev=b.get("evidence_and_data",{})
    lines.append("## 4. 证据与数据")
    lines.append("- 已支持claims: "+str(ev.get("claims_supported",0)))
    lines.append("- 未确认claims: "+str(ev.get("claims_unconfirmed",0)))
    lines.append("")
    mg=b.get("market_expectation_gap",{})
    lines.append("## 5. 市场预期与我们的差异")
    lines.append("- 预期差状态: "+str(mg.get("expectation_gap_status","")))
    lines.append("- 置信度: "+str(mg.get("expectation_gap_confidence","")))
    lines.append("")
    bb=b.get("bull_base_bear",{})
    lines.append("## 6. 多空分歧")
    lines.append("多头: "+"; ".join(bb.get("bull_case",[])[:2]))
    lines.append("空头: "+"; ".join(bb.get("bear_case",[])[:2]))
    lines.append("")
    vt=b.get("validation_triggers",{})
    lines.append("## 7. 下一步验证")
    [lines.append("- 增强: "+t.get("event","")) for t in vt.get("strengthening_triggers",[])[:2]]
    [lines.append("- 削弱: "+t.get("event","")) for t in vt.get("weakening_triggers",[])[:2]]
    lines.append("")
    ca=b.get("current_action",{})
    lines.append("## 8. 当前动作")
    lines.append("- 动作: "+str(ca.get("action","")))
    [lines.append("- "+r) for r in ca.get("next",[])]
    lines.append("")
    q=b.get("quality",{})
    lines.append("> 质量: 风格="+str(q.get("style_status",""))+" 深度="+str(q.get("depth_status",""))+" 禁词="+str(q.get("forbidden_phrase_violations",0))+" 系统词="+str(q.get("system_status_terms_found",0)))
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
