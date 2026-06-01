import json,os
from pathlib import Path
def build_refresh_history():
    history_path=Path(__file__).resolve().parent.parent.parent/"09_runbooks"/"generated"/"phase97_refresh_run_history.jsonl"
    runs=[]
    if history_path.exists():
        with open(history_path,"r",encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if line: runs.append(json.loads(line))
    return {"phase97_refresh_history":{"history_enabled":True,"history_path_ignored":True,"runs_available":len(runs),"latest_run":runs[-1] if runs else None,"mock_used":False,"fixture_used":False}}
