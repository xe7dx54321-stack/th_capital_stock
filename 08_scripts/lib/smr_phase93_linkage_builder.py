import json,os
from datetime import datetime
from pathlib import Path

def build_linkage(customer_exploration, supply_exploration):
    cust = customer_exploration.get("phase93_customer_source_exploration",{}).get("ticker_results",[])
    supp = supply_exploration.get("phase93_supply_source_exploration",{}).get("ticker_results",[])
    
    config_path = Path(__file__).resolve().parent.parent.parent/"config"/"phase93_customer_capex_supply_chain_sources.json"
    with open(config_path,"r",encoding="utf-8-sig") as fh:
        config = json.load(fh)
    key_customers = config.get("key_customers",{})
    key_suppliers = config.get("key_suppliers",{})
    
    linkage_results = []
    for ct,st in zip(cust, supp):
        ticker = ct["ticker"]
        lr = {
            "ticker":ticker,
            "blocked":ct.get("blocked",False),
            "customer_links":[],
            "supply_links":[],
            "linkage_summary":"no_significant_linkage" if ct.get("blocked") else "partial_linkage_identified"
        }
        
        customers = key_customers.get(ticker,[])
        for c in customers[:3]:
            lr["customer_links"].append({
                "customer":c,
                "linkage_type":"order_capex_context_supported" if ct["total_hits"]>0 else "order_context_unconfirmed",
                "linkage_confidence":"medium" if ct["total_hits"]>0 else "low",
                "cannot_conclude":["specific_order_linked","revenue_confirmed","market_share_change"]
            })
        
        suppliers = key_suppliers.get(ticker,[])
        for s in suppliers[:3]:
            lr["supply_links"].append({
                "supplier":s,
                "linkage_type":"order_supply_chain_context_supported" if st["total_hits"]>0 else "order_context_unconfirmed",
                "linkage_confidence":"medium" if st["total_hits"]>0 else "low",
                "cannot_conclude":["specific_supplier_dependency","cost_impact","delivery_timeline"]
            })
        
        linkage_results.append(lr)
    
    return {"phase93_linkage_builder":{
        "generated_at":datetime.now().isoformat(),
        "tickers_with_linkage":sum(1 for l in linkage_results if not l["blocked"]),
        "total_customer_links":sum(len(l["customer_links"]) for l in linkage_results),
        "total_supply_links":sum(len(l["supply_links"]) for l in linkage_results),
        "linkage_results":linkage_results,
        "mock_used":False,"fixture_used":False
    }}
