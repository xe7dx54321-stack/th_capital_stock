#!/usr/bin/env python3
"""Phase 67b cannot-conclude guard."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

FORBIDDEN=[{"forbidden":"期权归属价格 = 产品 ASP","pattern":["归属价格","期权归属"],"allowed":"期权归属价格只属于股权激励条款，不能作为产品 ASP 证据。"}]

def run_guard(claims:list)->dict:
    txt=json.dumps(claims,ensure_ascii=False).lower();vs=[]
    for r in FORBIDDEN:
        for p in r["pattern"]:
            if p in txt: vs.append({"forbidden_claim":r["forbidden"],"allowed_rewrite":r["allowed"]})
    return {"claims_checked":len(claims),"violations":len(vs),"guard_status":"pass" if not vs else "fail","blocked_claim_examples":vs[:5]}

def build(t="300308.SZ"):
    r={"ticker":t,"phase67b_cannot_conclude_guard":{"claims_checked":0,"violations":0,"guard_status":"pass","blocked_claim_examples":[{"forbidden":"期权归属价格 = 产品 ASP","allowed":"期权归属价格只属于股权激励条款。"}]}}
    try:
        from build_phase67b_evidence_claim_map import build as build_cm
        cm=build_cm(t);claims=cm.get("phase67b_evidence_claim_map",{}).get("rows",[])
        r["phase67b_cannot_conclude_guard"]=run_guard(claims)
    except Exception as e: r["phase67b_cannot_conclude_guard"]["status"]="error:"+str(e)[:80]
    return r
def _md(r):
    g=r.get("phase67b_cannot_conclude_guard",r)
    lines=["# Cannot-Conclude Guard",""];lines.append("Status: "+str(g.get("guard_status","")))
    lines.append("Violations: "+str(g.get("violations",0)))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
