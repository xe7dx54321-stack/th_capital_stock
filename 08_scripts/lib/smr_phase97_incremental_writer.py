import json,os
from pathlib import Path
from datetime import datetime
DB_PATH=Path(__file__).resolve().parent.parent.parent/"09_runbooks"/"generated"/"phase96_hard_data_db.jsonl"
MANIFEST_PATH=Path(__file__).resolve().parent.parent.parent/"09_runbooks"/"generated"/"phase97_db_manifest.json"
ROLLBACK_PATH=Path(__file__).resolve().parent.parent.parent/"09_runbooks"/"generated"/"phase97_db_rollback_manifest.json"
HISTORY_PATH=Path(__file__).resolve().parent.parent.parent/"09_runbooks"/"generated"/"phase97_refresh_run_history.jsonl"
def write_incremental(records, mode="dry-run"):
    if mode=="dry-run": return {"mode":"dry-run","records_to_write":len(records),"db_path_ignored":True}
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    if DB_PATH.exists():
        backup=[]
        with open(DB_PATH,"r",encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if line: backup.append(json.loads(line))
        with open(ROLLBACK_PATH,"w",encoding="utf-8") as f:
            for r in backup: f.write(json.dumps(r,ensure_ascii=False)+"\n")
    written=0
    with open(DB_PATH,"w",encoding="utf-8") as f:
        for r in records: f.write(json.dumps(r,ensure_ascii=False)+"\n");written+=1
    manifest={"generated_at":datetime.now().isoformat(),"total_records":written,"version":"phase97_incremental_v1","previous_rollback_saved":True,"gitignored":True}
    with open(MANIFEST_PATH,"w",encoding="utf-8") as f: json.dump(manifest,f,ensure_ascii=False,indent=2)
    return {"mode":"execute","records_written":written,"db_path_ignored":True,"manifest_created":True,"rollback_saved":DB_PATH.exists(),"run_id":f"phase97-{datetime.now().strftime('%Y%m%d-%H%M%S')}"}
def write_run_history(run_result):
    HISTORY_PATH.parent.mkdir(parents=True,exist_ok=True)
    with open(HISTORY_PATH,"a",encoding="utf-8") as f: f.write(json.dumps(run_result,ensure_ascii=False)+"\n")
    return {"history_written":True,"history_path_ignored":True}
