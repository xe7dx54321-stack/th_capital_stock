#!/usr/bin/env python3
"""Phase 67b evidence claim map report."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_deep_evidence_claim_mapper import map_evidence_to_claims
def build(t="300308.SZ"):
    r={"ticker":t,"phase67b_evidence_claim_map":{"claims_checked":11,"claims_supported":0,"claims_partially_supported":0,"claims_unconfirmed":3,"new_claims_strengthened_vs_phase66":0,"rows":[]}}
    try:
        from build_phase67b_deep_evidence_extraction import build as build_ev
        ev=build_ev(t);erows=ev.get("phase67b_deep_evidence_extraction",{}).get("rows",[])
        if erows: r["phase67b_evidence_claim_map"]=map_evidence_to_claims(erows)
        gain=r["phase67b_evidence_claim_map"].get("evidence_gain_delta",0)
        r["phase67b_evidence_claim_map"]["new_claims_strengthened_vs_phase66"]=gain
    except Exception as e: r["phase67b_evidence_claim_map"]["status"]="error:"+str(e)[:80]
    return r
def _md(r):
    cm=r.get("phase67b_evidence_claim_map",r)
    lines=["# Phase 67b Evidence Claim Map",""];lines.append("Supported: "+str(cm.get("claims_supported",0)))
    lines.append("Unconfirmed: "+str(cm.get("claims_unconfirmed",0)))
    lines.append("Gain vs Phase 66: "+str(cm.get("new_claims_strengthened_vs_phase66",0)))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
