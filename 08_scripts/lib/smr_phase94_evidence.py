import json,os
from datetime import datetime
def extract_evidence(pe,ge):
    pr=pe.get("phase94_pricing_exploration",{}).get("results",[])
    gr=ge.get("phase94_guidance_exploration",{}).get("results",[])
    evs=[]
    for pt,gt in zip(pr,gr):
        ev={"ticker":pt["ticker"],"blocked":pt.get("blocked",False),"pricing_ev":[],"guidance_ev":[]}
        if pt["hits"]>0 and not pt.get("blocked"):ev["pricing_ev"].append({"type":"pricing_text_found","claim":"product_pricing_or_ASP_related_text_identified","limit":"pricing_text_does_not_confirm_specific_ASP_or_margin","cannot":["specific_ASP","margin_confirmed","price_trend_confirmed","buy_signal"],"conf":"medium","mock":False})
        else:ev["pricing_ev"].append({"type":"no_pricing_text","claim":"no_pricing_text_found","limit":"exploration_not_exhaustive","cannot":["pricing_known","competitor_pricing"],"conf":"low","mock":False})
        if gt["hits"]>0 and not gt.get("blocked"):ev["guidance_ev"].append({"type":"guidance_text_found","claim":"management_guidance_related_text_identified","limit":"guidance_text_does_not_confirm_future_performance","cannot":["revenue_forecast","margin_forecast","specific_guidance_confirmed","buy_signal"],"conf":"medium","mock":False})
        else:ev["guidance_ev"].append({"type":"no_guidance_text","claim":"no_guidance_text_found","limit":"exploration_not_exhaustive","cannot":["guidance_known","management_view"],"conf":"low","mock":False})
        if pt.get("blocked"):ev["pricing_ev"].append({"type":"blocked","claim":"blocked_by_300394_cninfo","limit":"source_unavailable","cannot":["pricing_status"],"conf":"blocked","mock":False});ev["guidance_ev"].append({"type":"blocked","claim":"blocked_by_300394_cninfo","limit":"source_unavailable","cannot":["guidance_status"],"conf":"blocked","mock":False})
        evs.append(ev)
    pev=sum(1 for e in evs if any(it["type"]=="pricing_text_found" for it in e["pricing_ev"]))
    gev=sum(1 for e in evs if any(it["type"]=="guidance_text_found" for it in e["guidance_ev"]))
    return {"phase94_evidence":{"generated_at":datetime.now().isoformat(),"pricing_evidence":pev,"guidance_evidence":gev,"records":evs,"mock_used":False,"fixture_used":False}}
