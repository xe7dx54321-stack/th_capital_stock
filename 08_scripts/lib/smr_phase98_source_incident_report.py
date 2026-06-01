import json,os
from datetime import datetime
def build_incident_report(heartbeat, failure, staleness, blocked):
    incidents=[]
    be=blocked.get("phase98_blocked_escalation",{})
    for r in be.get("rows",[]):
        incidents.append({"incident_id":f"inc-blocked-{r['source']}","source":r["source"],"incident_type":"blocked_source","severity":r["alert_severity"],"tickers_affected":r.get("tickers_affected",[]),"recommended_action":r.get("recommended_action",""),"created_at":datetime.now().isoformat()[:10]})
    st=staleness.get("phase98_source_staleness",{})
    for s in st.get("expired_sources",[]):
        incidents.append({"incident_id":f"inc-expired-{s['source']}","source":s["source"],"incident_type":"source_expired","severity":"critical","tickers_affected":[],"recommended_action":"investigate_source_availability","created_at":datetime.now().isoformat()[:10]})
    return {"phase98_source_incident_report":{"total_incidents":len(incidents),"open_incidents":len(incidents),"resolved_incidents":0,"incidents":incidents,"mock_used":False,"fixture_used":False}}
