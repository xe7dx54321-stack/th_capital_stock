import json,os
from datetime import datetime
from pathlib import Path
def build_linkage(pe,ge):
    pr=pe.get("phase94_pricing_exploration",{}).get("results",[])
    gr=ge.get("phase94_guidance_exploration",{}).get("results",[])
    p2=Path(__file__).resolve().parent.parent.parent/"config"/"phase94_product_pricing_management_guidance.json"
    with open(p2,"r",encoding="utf-8-sig") as fh:cfg=json.load(fh)
    kp=cfg.get("key_products",{})
    res=[]
    for pt,gt in zip(pr,gr):
        lr={"ticker":pt["ticker"],"blocked":pt.get("blocked",False),"pricing_links":[],"guidance_links":[]}
        for prod in kp.get(pt["ticker"],[])[:3]:
            lr["pricing_links"].append({"product":prod,"type":"order_capex_pricing_context","conf":"medium" if pt["hits"]>0 else "low","cannot":["specific_ASP","revenue_confirmed"]})
        lr["guidance_links"].append({"event":"management_commentary","type":"guidance_context","conf":"medium" if gt["hits"]>0 else "low","cannot":["future_performance","revenue_forecast"]})
        res.append(lr)
    return {"phase94_linkage":{"generated_at":datetime.now().isoformat(),"tickers":len(res),"pricing_links":sum(len(l["pricing_links"]) for l in res),"guidance_links":sum(len(l["guidance_links"]) for l in res),"results":res,"mock_used":False,"fixture_used":False}}
