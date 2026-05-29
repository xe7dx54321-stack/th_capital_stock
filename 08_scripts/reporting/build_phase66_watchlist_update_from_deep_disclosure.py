#!/usr/bin/env python3
"""Phase 66 watchlist update from deep disclosure evidence."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build(t="300308.SZ"):
    r={"ticker":t,"watchlist_update_from_deep_disclosure":{"real_disclosure_evidence_used":False,"deep_evidence_created":0,"evidence_gain_delta":0,"claims_strengthened":[],"claims_still_unconfirmed":["customer_share_unconfirmed","asp_trend_unconfirmed","specific_order_volume_unconfirmed"],"risk_signals":[],"watchlist_decision":"continue_tracking","decision_reason":["真实披露证据仍在收集中。"],"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
    wu=r["watchlist_update_from_deep_disclosure"]
    try:
        from build_phase66_deep_evidence_claim_map import build as build_cm
        cm=build_cm(t)
        claims=cm.get("deep_evidence_claim_map",{})
        gain=claims.get("evidence_gain_delta",0)
        wu["evidence_gain_delta"]=gain
        strengthened=[row.get("claim","") for row in claims.get("rows",[]) if row.get("claim_status")=="supported"]
        wu["claims_strengthened"]=strengthened
        risk_signals=[row.get("claim","") for row in claims.get("rows",[]) if row.get("claim_status")=="risk_signal_found"]
        wu["risk_signals"]=risk_signals
        from build_phase66_deep_business_evidence_extraction import build as build_ev
        ev=build_ev(t)
        wu["deep_evidence_created"]=ev.get("deep_business_evidence_extraction",{}).get("evidence_created",0)
        wu["real_disclosure_evidence_used"]=wu["deep_evidence_created"]>0
        if gain>=2:
            wu["watchlist_decision"]="continue_tracking_deep_disclosure_evidence_strengthened"
            wu["decision_reason"]=["真实披露文本增加了业务证据支持。","客户份额、ASP、具体订单量仍没有直接披露证据。"]
        elif gain>=1:
            wu["watchlist_decision"]="continue_tracking_real_disclosure_evidence_strengthened"
            wu["decision_reason"]=["真实披露证据有增量，但仍需更多文本验证。","客户份额、ASP、订单量仍 unconfirmed。"]
        else:
            wu["watchlist_decision"]="continue_tracking"
            wu["decision_reason"]=["真实披露证据增量有限，需要继续收集。","客户份额、ASP、订单量仍 unconfirmed。"]
    except Exception as e:
        wu["status"]="error:"+str(e)[:80]
    return r

def _md(r):
    wu=r.get("watchlist_update_from_deep_disclosure",r)
    lines=["# Watchlist Update from Deep Disclosure",""]
    lines.append("Evidence used: "+str(wu.get("real_disclosure_evidence_used")))
    lines.append("Deep evidence created: "+str(wu.get("deep_evidence_created",0)))
    lines.append("Delta: "+str(wu.get("evidence_gain_delta",0)))
    lines.append("Decision: "+str(wu.get("watchlist_decision","")))
    lines.append("Strengthened:")
    for c in wu.get("claims_strengthened",[]):
        lines.append("  - "+str(c))
    lines.append("Unconfirmed:")
    for c in wu.get("claims_still_unconfirmed",[]):
        lines.append("  - "+str(c))
    if wu.get("risk_signals"):
        lines.append("Risk signals:")
        for r in wu["risk_signals"]:
            lines.append("  - "+str(r))
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
