import json,os
from datetime import datetime
from pathlib import Path

def build_ticker_entity_resolver():
    config_path = Path(__file__).resolve().parent.parent.parent/"config"/"phase92_order_contract_tender_sources.json"
    with open(config_path,"r",encoding="utf-8-sig") as fh:
        config = json.load(fh)
    entities = config.get("ticker_entities",{})
    
    rows = []
    for ticker in config["universe"]:
        entity = entities.get(ticker,{"display_name":ticker,"search_terms":[ticker],"market":"unknown"})
        rows.append({
            "ticker":ticker,
            "market":entity.get("market","unknown"),
            "display_name":entity.get("display_name",ticker),
            "search_terms":entity.get("search_terms",[ticker]),
            "entity_status":"blocked" if entity.get("blocked") else "resolved",
            "blocked":entity.get("blocked",False)
        })
    
    return {"phase92_ticker_entity_resolver":{
        "generated_at":datetime.now().isoformat(),
        "tickers_resolved":len(rows),
        "entities":rows,
        "mock_used":False,"fixture_used":False
    }}
