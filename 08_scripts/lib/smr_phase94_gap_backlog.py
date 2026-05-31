import json,os
from datetime import datetime
def build_gap_closeout(coverage):
    pc=coverage.get("phase94_pricing_coverage",{}).get("rows",[])
    gc=coverage.get("phase94_guidance_coverage",{}).get("rows",[])
    items=[]
    for p,g in zip(pc,gc):
        items.append({"ticker":p["ticker"],"pricing_pre":"gap","pricing_post":p["status"],"guidance_pre":"gap","guidance_post":g["status"],"closed":False,"note":"text_explored_structured_data_still_gap","next":"structured_pricing_guidance_db"})
    return {"phase94_gap_closeout":{"generated_at":datetime.now().isoformat(),"total":len(items),"pricing_partial":sum(1 for i in items if "text_found" in i["pricing_post"]),"guidance_partial":sum(1 for i in items if "text_found" in i["guidance_post"]),"items":items,"summary":"pricing_and_guidance_text_explored_structured_data_remains_gap","mock_used":False,"fixture_used":False}}
def build_backlog():
    bl=[{"r":1,"gap":"product_pricing","status":"partially_addressed","phase":"phase94"},{"r":2,"gap":"management_guidance","status":"partially_addressed","phase":"phase94"},{"r":3,"gap":"order_contract","status":"partially_addressed","phase":"phase92"},{"r":4,"gap":"customer_capex","status":"partially_addressed","phase":"phase93"},{"r":5,"gap":"supply_chain","status":"partially_addressed","phase":"phase93"},{"r":6,"gap":"structured_order_db","status":"foundation_created","phase":"phase93"},{"r":7,"gap":"order_customer_supply_linkage","status":"foundation_created","phase":"phase93"},{"r":8,"gap":"300394_resolution","status":"unchanged","phase":"phase95"},{"r":9,"gap":"688041_valuation","status":"unchanged","phase":"phase96"},{"r":10,"gap":"peer_benchmark","status":"unchanged","phase":"phase96"}]
    return {"phase94_backlog":{"generated_at":datetime.now().isoformat(),"items":len(bl),"phase95_recommendation":"300394_cninfo_resolution_and_688041_valuation_gap_close","backlog":bl,"mock_used":False,"fixture_used":False}}
