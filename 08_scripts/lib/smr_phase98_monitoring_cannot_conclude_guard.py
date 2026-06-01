import json,os
def run_monitoring_guard(alert_result):
    al=alert_result.get("phase98_alert_classifier",{})
    alerts=al.get("alerts",[])
    violations=[]
    for a in alerts:
        if isinstance(a,dict):
            if "buy" in str(a.get("detail","")).lower() or "sell" in str(a.get("detail","")).lower():
                violations.append({"alert_id":a["alert_id"],"violation":"trade_advice_in_alert"})
            if "target_price" in str(a.get("detail","")).lower():
                violations.append({"alert_id":a["alert_id"],"violation":"target_price_in_alert"})
    return {"phase98_monitoring_guard":{"overall":"pass" if len(violations)==0 else "fail","violations":len(violations),"violation_details":violations,"mock_used":False,"fixture_used":False}}
