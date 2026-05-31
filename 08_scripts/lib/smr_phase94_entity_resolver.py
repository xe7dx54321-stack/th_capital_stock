import json,os
from datetime import datetime
from pathlib import Path
def build_entity_resolver():
    p=Path(__file__).resolve().parent.parent.parent/"config"/"phase94_product_pricing_management_guidance.json"
    with open(p,"r",encoding="utf-8-sig") as fh:cfg=json.load(fh)
    kp=cfg.get("key_products",{})
    rows=[]
    for t in cfg["universe"]:
        prods=kp.get(t,[])
        rows.append({"ticker":t,"key_products":prods,"product_count":len(prods),"status":"blocked" if t=="300394.SZ" else "resolved"})
    return {"phase94_entity_resolver":{"generated_at":datetime.now().isoformat(),"tickers_resolved":len(rows),"total_products_mapped":sum(r["product_count"] for r in rows),"entities":rows,"mock_used":False,"fixture_used":False}}
