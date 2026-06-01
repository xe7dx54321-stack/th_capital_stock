import json,os
def select_fallback_sources(heartbeat_result):
    hb=heartbeat_result.get("phase98_heartbeat_probe",{})
    results=hb.get("results",[])
    selected=[]
    for r in results:
        if r["heartbeat_status"]=="blocked":
            selected.append({"source":r["source"],"status":"blocked","fallback_selected":"irm_news","fallback_type":"limited_replacement","priority":"high"})
        elif r["heartbeat_status"]=="skipped":
            selected.append({"source":r["source"],"status":"skipped","fallback_selected":None,"fallback_type":"none","priority":"medium"})
        else:
            selected.append({"source":r["source"],"status":"healthy","fallback_selected":None,"fallback_type":"none","priority":"low"})
    return {"phase99_fallback_selector":{"total_sources":len(results),"fallback_needed":sum(1 for s in selected if s["fallback_selected"]),"fallback_not_needed":sum(1 for s in selected if not s["fallback_selected"]),"rows":selected,"mock_used":False,"fixture_used":False}}
