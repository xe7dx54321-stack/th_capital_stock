#!/usr/bin/env python3
"""Phase 66 deep evidence claim map."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_deep_evidence_claim_mapper import map_evidence_to_claims

def build(t="300308.SZ"):
    r={"ticker":t,"deep_evidence_claim_map":{"claims_checked":11,"claims_supported":0,"claims_partially_supported":0,"claims_unconfirmed":3,"claims_with_risk_signal":0,"evidence_gain_delta":0,"rows":[]}}
    try:
        from build_phase66_deep_business_evidence_extraction import build as build_ev
        ev=build_ev(t)
        rows=ev.get("deep_business_evidence_extraction",{}).get("rows",[])
        if rows:
            cm=map_evidence_to_claims(rows)
            r["deep_evidence_claim_map"]=cm
        else:
            r["deep_evidence_claim_map"]["status"]="no_evidence_to_map"
    except Exception as e:
        r["deep_evidence_claim_map"]["status"]="error:"+str(e)[:80]
    return r

def _md(r):
    cm=r.get("deep_evidence_claim_map",r)
    lines=["# Deep Evidence Claim Map",""]
    lines.append("Checked: "+str(cm.get("claims_checked",0)))
    lines.append("Supported: "+str(cm.get("claims_supported",0)))
    lines.append("Partially supported: "+str(cm.get("claims_partially_supported",0)))
    lines.append("Unconfirmed: "+str(cm.get("claims_unconfirmed",0)))
    lines.append("Risk signals: "+str(cm.get("claims_with_risk_signal",0)))
    lines.append("Gain delta: "+str(cm.get("evidence_gain_delta",0)))
    for row in cm.get("rows",[])[:5]:
        lines.append("- "+str(row.get("claim",""))+" ["+str(row.get("claim_status",""))+"]")
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
