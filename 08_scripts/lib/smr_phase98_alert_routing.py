import json,os
def route_alerts(alert_result):
    al=alert_result.get("phase98_alert_classifier",{})
    alerts=al.get("alerts",[])
    routed=[]
    for a in alerts:
        r={"alert_id":a["alert_id"],"source":a["source"],"severity":a["severity"],"local_report":True,"external_notification":False,"external_disabled_by_config":True}
        routed.append(r)
    return {"phase98_alert_routing":{"total_alerts":len(alerts),"routed_to_local":len(alerts),"routed_to_external":0,"external_disabled":True,"rows":routed,"mock_used":False,"fixture_used":False}}
