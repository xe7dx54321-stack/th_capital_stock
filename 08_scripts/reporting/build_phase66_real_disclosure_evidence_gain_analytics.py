#!/usr/bin/env python3
"""Phase 66 real disclosure evidence gain analytics."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build(t="300308.SZ"):
    r={"ticker":t,"real_disclosure_evidence_gain_analytics":{"phase65b":{"texts_usable_for_evidence":1,"evidence_gain_delta":1},"phase66":{"texts_usable_for_evidence":0,"deep_evidence_created":0,"evidence_gain_delta":0},"incremental_gain":{"usable_text_delta":0,"evidence_delta":0,"new_claims_strengthened":[]},"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
    try:
        from build_phase66_business_evidence_text_quality import build as build_qual
        qual=build_qual(t)
        q=qual.get("business_evidence_text_quality",{})
        usable=q.get("high_business_signal",0)+q.get("usable_business_signal",0)
        r["real_disclosure_evidence_gain_analytics"]["phase66"]["texts_usable_for_evidence"]=usable
        from build_phase66_deep_business_evidence_extraction import build as build_ev
        ev=build_ev(t)
        deep=ev.get("deep_business_evidence_extraction",{})
        deep_created=deep.get("evidence_created",0)
        r["real_disclosure_evidence_gain_analytics"]["phase66"]["deep_evidence_created"]=deep_created
        from build_phase66_deep_evidence_claim_map import build as build_cm
        cm=build_cm(t)
        claims=cm.get("deep_evidence_claim_map",{})
        gain=claims.get("evidence_gain_delta",0)
        r["real_disclosure_evidence_gain_analytics"]["phase66"]["evidence_gain_delta"]=gain
        strengthened=[row.get("claim","") for row in claims.get("rows",[]) if row.get("claim_status")=="supported"]
        r["real_disclosure_evidence_gain_analytics"]["incremental_gain"]["usable_text_delta"]=max(0,usable-1)
        r["real_disclosure_evidence_gain_analytics"]["incremental_gain"]["evidence_delta"]=max(0,gain-1)
        r["real_disclosure_evidence_gain_analytics"]["incremental_gain"]["new_claims_strengthened"]=strengthened
    except Exception as e:
        r["real_disclosure_evidence_gain_analytics"]["status"]="partial:"+str(e)[:80]
    return r

def _md(r):
    ga=r.get("real_disclosure_evidence_gain_analytics",r)
    lines=["# Evidence Gain Analytics",""]
    p65b=ga.get("phase65b",{})
    p66=ga.get("phase66",{})
    inc=ga.get("incremental_gain",{})
    lines.append("Phase 65b: texts="+str(p65b.get("texts_usable_for_evidence",0))+", delta="+str(p65b.get("evidence_gain_delta",0)))
    lines.append("Phase 66: texts="+str(p66.get("texts_usable_for_evidence",0))+", deep="+str(p66.get("deep_evidence_created",0))+", delta="+str(p66.get("evidence_gain_delta",0)))
    lines.append("Incremental: text delta="+str(inc.get("usable_text_delta",0))+", evidence delta="+str(inc.get("evidence_delta",0)))
    for c in inc.get("new_claims_strengthened",[]):
        lines.append("- Strengthened: "+str(c))
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
