import json,os
def map_alerts_to_actions(alert_result):
    al=alert_result.get("phase98_alert_classifier",{})
    alerts=al.get("alerts",[])
    actions=[]
    for a in alerts:
        at=a.get("alert_type","")
        if at in ("endpoint_blocked","refresh_failure"):
            actions.append({"alert_id":a["alert_id"],"source":a["source"],"alert_type":at,"recovery_action":"primary_retry_or_fallback","priority":"high","detail":"retry primary or attempt fallback"})
        elif at=="field_regression":
            actions.append({"alert_id":a["alert_id"],"source":a["source"],"alert_type":at,"recovery_action":"alternative_field_mapping","priority":"medium","detail":"attempt alternate field mapping"})
        elif at=="source_expired":
            actions.append({"alert_id":a["alert_id"],"source":a["source"],"alert_type":at,"recovery_action":"stale_refresh_or_replacement","priority":"high","detail":"re-refresh or consider replacement"})
        elif at=="reliability_decay":
            actions.append({"alert_id":a["alert_id"],"source":a["source"],"alert_type":at,"recovery_action":"degraded_parser_or_fallback","priority":"medium","detail":"degrade parser or switch to fallback"})
        elif at=="blocked_escalation":
            actions.append({"alert_id":a["alert_id"],"source":a["source"],"alert_type":at,"recovery_action":"manual_or_limited_replacement","priority":"escalation","detail":"attempt restricted replacement, manual resolution needed"})
        else:
            actions.append({"alert_id":a["alert_id"],"source":a["source"],"alert_type":at,"recovery_action":"monitor_only","priority":"info","detail":"no auto-recovery attempted"})
    return {"phase99_alert_to_recovery_mapper":{"alerts_mapped":len(alerts),"actions_created":len(actions),"actions":actions,"mock_used":False,"fixture_used":False}}
