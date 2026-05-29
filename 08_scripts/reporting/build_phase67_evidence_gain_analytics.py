#!/usr/bin/env python3
"""Phase 67 evidence gain analytics."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build(t="300308.SZ"):
    r={"ticker":t,"phase67_evidence_gain_analytics":{"phase66":{"texts_usable_for_evidence":3,"deep_evidence_created":5,"evidence_gain_delta":0},"phase67":{"texts_usable_for_evidence":0,"deep_evidence_created":0,"evidence_gain_delta":0},"incremental_gain":{"usable_text_delta":0,"deep_evidence_delta":0,"claim_strengthening_delta":0},"new_claims_strengthened":[],"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
    try:
        from build_phase67_ir_report_text_quality import build as build_qt
        qt=build_qt(t)
        tq=qt.get("ir_report_text_quality",{})
        usable=tq.get("texts_usable_for_deep_extraction",0)
        r["phase67_evidence_gain_analytics"]["phase67"]["texts_usable_for_evidence"]=usable
        from build_phase67_deep_evidence_rerun import build as build_ev
        ev=build_ev(t)
        de=ev.get("phase67_deep_evidence_rerun",{})
        r["phase67_evidence_gain_analytics"]["phase67"]["deep_evidence_created"]=de.get("deep_evidence_created",0)
        gain=de.get("evidence_gain_delta",0)
        r["phase67_evidence_gain_analytics"]["phase67"]["evidence_gain_delta"]=gain
        r["phase67_evidence_gain_analytics"]["incremental_gain"]["usable_text_delta"]=max(0,usable-3)
        r["phase67_evidence_gain_analytics"]["incremental_gain"]["deep_evidence_delta"]=max(0,de.get("deep_evidence_created",0)-5)
        r["phase67_evidence_gain_analytics"]["incremental_gain"]["claim_strengthening_delta"]=gain
    except Exception as e:
        r["phase67_evidence_gain_analytics"]["status"]="partial:"+str(e)[:80]
    return r

def _md(r):
    ga=r.get("phase67_evidence_gain_analytics",r)
    p66=ga.get("phase66",{});p67=ga.get("phase67",{});inc=ga.get("incremental_gain",{})
    lines=["# Phase 67 Evidence Gain Analytics",""]
    lines.append("Phase 66: texts="+str(p66.get("texts_usable_for_evidence",0))+", deep="+str(p66.get("deep_evidence_created",0))+", delta="+str(p66.get("evidence_gain_delta",0)))
    lines.append("Phase 67: texts="+str(p67.get("texts_usable_for_evidence",0))+", deep="+str(p67.get("deep_evidence_created",0))+", delta="+str(p67.get("evidence_gain_delta",0)))
    lines.append("Delta: texts="+str(inc.get("usable_text_delta",0))+", deep="+str(inc.get("deep_evidence_delta",0))+", claims="+str(inc.get("claim_strengthening_delta",0)))
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
