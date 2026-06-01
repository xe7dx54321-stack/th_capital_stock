import json,os
from datetime import datetime
def classify_alerts(heartbeat_result, failure_result, schema_drift, field_avail, staleness, reliability, blocked):
    alerts=[]
    hb=heartbeat_result.get("phase98_heartbeat_probe",{})
    for r in hb.get("results",[]):
        if r["heartbeat_status"]=="blocked":
            alerts.append({"alert_id":f"hb-{r['source']}", "source":r["source"], "alert_type":"endpoint_blocked","severity":"info","detail":"blocked_source","created_at":datetime.now().isoformat()})
    fr=failure_result.get("phase98_refresh_failure_detector",{})
    for f in fr.get("failures",[]):
        if f.get("alert_severity") in ("warning","critical"):
            alerts.append({"alert_id":f"rf-{f['source']}", "source":f["source"], "alert_type":"refresh_failure","severity":f["alert_severity"],"detail":f["failure_reason"],"created_at":datetime.now().isoformat()})
    fa=field_avail.get("phase98_field_availability",{})
    for r in fa.get("rows",[]):
        if r.get("regression_detected"):
            alerts.append({"alert_id":f"fa-{r['source']}", "source":r["source"], "alert_type":"field_regression","severity":"warning","detail":f"fields_regressed={len(r.get('missing_fields',[]))}","created_at":datetime.now().isoformat()})
    st=staleness.get("phase98_source_staleness",{})
    for s in st.get("expired_sources",[]):
        alerts.append({"alert_id":f"st-{s['source']}", "source":s["source"], "alert_type":"source_expired","severity":"critical","detail":f"days={s.get('days_since_last_update',-1)}","created_at":datetime.now().isoformat()})
    rd=reliability.get("phase98_reliability_decay",{})
    for r in rd.get("rows",[]):
        if r["decay_status"]=="blocked":
            alerts.append({"alert_id":f"rd-{r['source']}", "source":r["source"], "alert_type":"reliability_decay","severity":"warning","detail":f"score={r['reliability_score']}","created_at":datetime.now().isoformat()})
    be=blocked.get("phase98_blocked_escalation",{})
    for r in be.get("rows",[]):
        if r["alert_severity"]=="escalation":
            alerts.append({"alert_id":f"be-{r['source']}", "source":r["source"], "alert_type":"blocked_escalation","severity":"escalation","detail":f"days_blocked={r['days_blocked']}","created_at":datetime.now().isoformat()})
    sev={"info":0,"warning":0,"critical":0,"escalation":0}
    for a in alerts: sev[a["severity"]]+=1
    return {"phase98_alert_classifier":{"alerts_created":len(alerts),"severity_breakdown":sev,"alerts":alerts,"mock_used":False,"fixture_used":False}}
