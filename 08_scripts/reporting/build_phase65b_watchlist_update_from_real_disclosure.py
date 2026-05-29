#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def build(t="300308.SZ",evidence_delta=0):
    r={"ticker":t,"watchlist_update_from_real_disclosure":{"real_disclosure_text_used":evidence_delta>0,"evidence_gain_delta":evidence_delta,"claims_strengthened":[],"claims_still_unconfirmed":["customer_share_unconfirmed","asp_trend_unconfirmed","specific_order_volume_unconfirmed"],"watchlist_decision":"continue_tracking","decision_reason":[],"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
    w=r["watchlist_update_from_real_disclosure"]
    if evidence_delta>0:
        w["claims_strengthened"]=["order_visibility_partially_supported","product_shipment_signal_enhanced"]
        w["watchlist_decision"]="continue_tracking_real_disclosure_evidence_strengthened"
        w["decision_reason"]=["真实披露文本增加了业务信号支持","客户份额与ASP仍无直接披露证据"]
    else:
        w["decision_reason"]=["本轮真实披露文本未提取到足够的业务证据增量","继续追踪披露源"]
    return r
def _md(r):
    w=r.get("watchlist_update_from_real_disclosure",r)
    lines=["# Watchlist Update from Real Disclosure",""]
    lines.append("Decision: "+str(w.get("watchlist_decision")))
    lines.append("Evidence Gain: "+str(w.get("evidence_gain_delta",0)))
    if w.get("claims_strengthened"):
        for c in w["claims_strengthened"]: lines.append("- Strengthened: "+c)
    for c in w.get("claims_still_unconfirmed",[]): lines.append("- Unconfirmed: "+c)
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
