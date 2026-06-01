import json,os
from pathlib import Path
from datetime import datetime
ALERT_PATH=Path(__file__).resolve().parent.parent.parent/"09_runbooks"/"generated"/"phase98_alert_history.jsonl"
def write_alert_history(alerts, mode="dry-run"):
    al=alerts.get("phase98_alert_classifier",{}).get("alerts",[])
    if mode=="dry-run":
        return {"phase98_alert_history":{"mode":"dry-run","alerts_to_write":len(al),"alert_history_path_ignored":True}}
    ALERT_PATH.parent.mkdir(parents=True,exist_ok=True)
    written=0
    with open(ALERT_PATH,"a",encoding="utf-8") as f:
        for a in al:
            entry={"written_at":datetime.now().isoformat(),"alert_id":a["alert_id"],"source":a["source"],"alert_type":a["alert_type"],"severity":a["severity"],"detail":a["detail"]}
            f.write(json.dumps(entry,ensure_ascii=False)+"\n")
            written+=1
    return {"phase98_alert_history":{"mode":"execute","alerts_written":written,"alert_history_path_ignored":True}}
def read_alert_history():
    alerts=[]
    if ALERT_PATH.exists():
        with open(ALERT_PATH,"r",encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if line: alerts.append(json.loads(line))
    return {"phase98_alert_history_read":{"alerts_loaded":len(alerts),"alert_history_path_ignored":True,"latest_alerts":alerts[-3:] if alerts else []}}
