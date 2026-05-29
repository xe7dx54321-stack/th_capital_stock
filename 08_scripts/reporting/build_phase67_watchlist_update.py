#!/usr/bin/env python3
"""Phase 67 watchlist update from IR/report evidence."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build(t="300308.SZ"):
    r={"ticker":t,"phase67_watchlist_update":{"real_ir_report_evidence_used":False,"evidence_gain_delta":0,"claims_strengthened":[],"claims_still_unconfirmed":["customer_share_unconfirmed","asp_trend_unconfirmed","specific_order_volume_unconfirmed"],"risk_signals":[],"watchlist_decision":"continue_tracking","pending_created":0,"paper_order_created":0,"real_trade_created":0}}
    wu=r["phase67_watchlist_update"]
    try:
        from build_phase67_deep_evidence_rerun import build as build_ev
        ev=build_ev(t)
        de=ev.get("phase67_deep_evidence_rerun",{})
        gain=de.get("evidence_gain_delta",0)
        wu["evidence_gain_delta"]=gain
        wu["real_ir_report_evidence_used"]=de.get("deep_evidence_created",0)>0
        if gain>=2:
            wu["watchlist_decision"]="continue_tracking_ir_report_evidence_strengthened"
            wu["claims_strengthened"]=["800G_signal_supported","order_visibility_partially_supported","capacity_expansion_supported"]
        elif gain>=1:
            wu["watchlist_decision"]="continue_tracking_pagination_searchkey_evidence_partial"
        else:
            wu["watchlist_decision"]="continue_tracking"
    except Exception as e:
        wu["status"]="error:"+str(e)[:80]
    return r

def _md(r):
    wu=r.get("phase67_watchlist_update",r)
    lines=["# Phase 67 Watchlist Update",""]
    lines.append("Evidence used: "+str(wu.get("real_ir_report_evidence_used")))
    lines.append("Gain delta: "+str(wu.get("evidence_gain_delta",0)))
    lines.append("Decision: "+str(wu.get("watchlist_decision","")))
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
