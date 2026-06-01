import json,os
def detect_refresh_failure(heartbeat_result):
    hb=heartbeat_result.get("phase98_heartbeat_probe",{})
    results=hb.get("results",[])
    failures=[]
    for r in results:
        if r["heartbeat_status"]=="blocked":
            failures.append({"source":r["source"],"failure_reason":"blocked_source","consecutive_failures":-1,"alert_severity":"info"})
        elif r["heartbeat_status"]=="skipped":
            failures.append({"source":r["source"],"failure_reason":"network_unavailable","consecutive_failures":0,"alert_severity":"warning"})
    return {"phase98_refresh_failure_detector":{"total_sources":len(results),"failed_sources":len(failures),"consecutive_failures_alert_threshold":3,"failures":failures,"mock_used":False,"fixture_used":False}}
