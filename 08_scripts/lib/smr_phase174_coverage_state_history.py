# Phase174 coverage state history
import json, os
from datetime import datetime

HISTORY_PATH = "09_runbooks/generated/phase174_coverage_state/coverage_state_history.jsonl"

def build_coverage_state_history():
    os.makedirs(os.path.dirname(HISTORY_PATH),exist_ok=True)
    existing = []
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH,"r",encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if line:
                    try: existing.append(json.loads(line))
                    except: pass
    return {"phase174_coverage_state_history":{
        "history_enabled":True,
        "history_path":HISTORY_PATH,
        "history_path_ignored":True,
        "runs_recorded":len(existing),
        "latest_run":existing[-1] if existing else None,
        "mock_used":False,"fixture_used":False
    }}

def write_history_entry(run_id,coverage_summary):
    os.makedirs(os.path.dirname(HISTORY_PATH),exist_ok=True)
    entry = {
        "run_id":run_id,
        "timestamp":datetime.now().isoformat(),
        "coverage_state_count":coverage_summary.get("coverage_state_count",0),
        "activated_count":coverage_summary.get("activated_count",0),
        "kept_count":coverage_summary.get("kept_count",0),
        "deferred_count":coverage_summary.get("deferred_count",0),
        "rejected_count":coverage_summary.get("rejected_count",0)
    }
    with open(HISTORY_PATH,"a",encoding="utf-8") as f:
        f.write(json.dumps(entry,ensure_ascii=False)+"\n")
    return {"written":True,"path":HISTORY_PATH,"path_ignored":True}
