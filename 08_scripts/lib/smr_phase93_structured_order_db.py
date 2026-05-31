import json,os
from datetime import datetime
from pathlib import Path

ORDER_DB_PATH = "09_runbooks/generated/phase93_structured_order_db.jsonl"

def build_order_db_foundation(mode="dry-run"):
    config_path = Path(__file__).resolve().parent.parent.parent/"config"/"phase93_customer_capex_supply_chain_sources.json"
    with open(config_path,"r",encoding="utf-8-sig") as fh:
        config = json.load(fh)
    
    db_config = config.get("structured_order_db",{})
    fields = db_config.get("fields",[])
    
    records = []
    if mode == "execute":
        os.makedirs(os.path.dirname(ORDER_DB_PATH), exist_ok=True)
        # Write header/schema record
        schema = {"record_type":"schema","fields":fields,"created_at":datetime.now().isoformat(),"phase":"phase93"}
        with open(ORDER_DB_PATH,"w",encoding="utf-8") as f:
            f.write(json.dumps(schema,ensure_ascii=False)+"\n")
        records.append(schema)
    
    return {"phase93_structured_order_db_foundation":{
        "generated_at":datetime.now().isoformat(),
        "db_path":ORDER_DB_PATH,
        "db_path_ignored":True,
        "fields":fields,
        "mode":mode,
        "schema_written":mode=="execute",
        "mock_used":False,"fixture_used":False
    }}
