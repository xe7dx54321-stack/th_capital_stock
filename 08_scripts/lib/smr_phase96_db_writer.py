import json,os
from pathlib import Path
from datetime import datetime
def write_hard_data_db(records,mode="dry-run"):
    from smr_phase96_config import get_db_path
    db_rel=get_db_path()
    db_path=Path(__file__).resolve().parent.parent.parent/db_rel
    manifest_path=db_path.parent/"phase96_hard_data_manifest.json"
    if mode=="dry-run":
        return {"mode":"dry-run","records_would_write":len(records),"db_path":str(db_path),"db_path_ignored":True,"manifest_path_ignored":True}
    db_path.parent.mkdir(parents=True,exist_ok=True)
    written=0
    with open(db_path,"w",encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r,ensure_ascii=False)+"\n");written+=1
    manifest={"generated_at":datetime.now().isoformat(),"total_records":written,"source":"phase96_hard_data_db_population","gitignored":True}
    with open(manifest_path,"w",encoding="utf-8") as f: json.dump(manifest,f,ensure_ascii=False,indent=2)
    return {"mode":"execute","records_written":written,"db_path":str(db_path),"db_path_ignored":True,"manifest_path":str(manifest_path),"manifest_path_ignored":True}
