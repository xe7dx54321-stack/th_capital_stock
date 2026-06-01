import json,os
from pathlib import Path
from datetime import datetime
PATH=Path(__file__).resolve().parent.parent.parent/"09_runbooks"/"generated"/"phase99_recovery_history.jsonl"
def write_recovery_history(retry, fallback, degraded, field_map, stale, replacement, mode="dry-run"):
    entries=[]
    for mod,name in [(retry,"primary_retry"),(fallback,"fallback"),(degraded,"degraded_parser"),(field_map,"alt_field_mapping"),(stale,"stale_refresh"),(replacement,"blocked_replacement")]:
        key=f"phase99_{name}"
        for r in mod.get(key,{}).get("results",[]):
            entries.append({"written_at":datetime.now().isoformat(),"recovery_type":name,"source":r.get("source",""),"status":r.get("result",""),"recovered":r.get("recovered",False)})
    if mode=="dry-run":
        return {"phase99_recovery_history":{"mode":"dry-run","entries_to_write":len(entries),"recovery_history_path_ignored":True}}
    PATH.parent.mkdir(parents=True,exist_ok=True)
    written=0
    with open(PATH,"a",encoding="utf-8") as f:
        for e in entries: f.write(json.dumps(e,ensure_ascii=False)+"\n"); written+=1
    return {"phase99_recovery_history":{"mode":"execute","entries_written":written,"recovery_history_path_ignored":True}}
