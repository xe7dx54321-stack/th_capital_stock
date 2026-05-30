import json,os,datetime
from pathlib import Path
HP=Path(__file__).resolve().parents[2]/"09_runbooks"/"generated"/"phase84_daily_monitoring_history.jsonl"
def write_history(run_state):
    os.makedirs(HP.parent,exist_ok=True)
    with open(HP,"a",encoding="utf-8") as f:f.write(json.dumps(run_state,ensure_ascii=False)+"\n")
def load_history():
    if not HP.exists():return []
    runs=[]
    with open(HP,"r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:runs.append(json.loads(line))
    return runs
def history_report():
    runs=load_history()
    return {"phase84_daily_run_history":{"history_enabled":True,"history_path":str(HP),"history_path_ignored":True,"runs_loaded":len(runs),"latest_run_id":runs[-1]["run_id"] if runs else "none","mock_used":False,"fixture_used":False}}
