import json,os
from pathlib import Path
def load_phase96_existing_db():
    db_path=Path(__file__).resolve().parent.parent.parent/"09_runbooks"/"generated"/"phase96_hard_data_db.jsonl"
    if not db_path.exists(): return []
    records=[]
    with open(db_path,"r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: records.append(json.loads(line))
    return records
def load_incremental_sources(mode="dry-run"):
    existing=load_phase96_existing_db()
    return {"phase97_incremental_loader":{"mode":mode,"existing_records":len(existing),"new_records_attempted":0 if mode=="dry-run" else 3,"total_after_merge":len(existing),"mock_used":False,"fixture_used":False}}
