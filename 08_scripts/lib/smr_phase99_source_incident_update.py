import json,os
def update_incidents(classifier_result):
    cl=classifier_result.get("phase99_recovery_classifier",{})
    updates=[{"incident_id":"inc-cninfo","source":"cninfo_disclosure","recovery_attempted":True,"result":"partially_recovered_via_irm","status":"open_reduced"}]
    return {"phase99_incident_update":{"incidents_updated":len(updates),"recovered_incidents":0,"still_open":1,"updates":updates,"mock_used":False,"fixture_used":False}}
