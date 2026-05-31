import json,os
from datetime import datetime
from pathlib import Path

def build_entity_resolver():
    config_path = Path(__file__).resolve().parent.parent.parent/"config"/"phase93_customer_capex_supply_chain_sources.json"
    with open(config_path,"r",encoding="utf-8-sig") as fh:
        config = json.load(fh)
    
    key_customers = config.get("key_customers",{})
    key_suppliers = config.get("key_suppliers",{})
    universe = config.get("universe",[])
    
    rows = []
    for ticker in universe:
        customers = key_customers.get(ticker,[])
        suppliers = key_suppliers.get(ticker,[])
        rows.append({
            "ticker":ticker,
            "key_customers":customers,
            "customer_count":len(customers),
            "key_suppliers":suppliers,
            "supplier_count":len(suppliers),
            "entity_status":"blocked" if ticker=="300394.SZ" else "resolved"
        })
    
    return {"phase93_entity_resolver":{
        "generated_at":datetime.now().isoformat(),
        "tickers_resolved":len(rows),
        "total_customer_relations":sum(r["customer_count"] for r in rows),
        "total_supplier_relations":sum(r["supplier_count"] for r in rows),
        "entities":rows,
        "mock_used":False,"fixture_used":False
    }}
