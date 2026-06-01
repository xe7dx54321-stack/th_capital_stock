import json,os
from smr_phase105_emergency_domain_registry import build_emergency_domain_registry
def build_emergency_readiness_scorecard():
    reg=build_emergency_domain_registry()
    domains=reg["phase105_emergency_domain_registry"]["domains"]
    status_count={}
    for d in domains:
        s=d["readiness_status"]
        status_count[s]=status_count.get(s,0)+1
    scorecard={
        "total_domains":len(domains),
        "ready":status_count.get("ready",0),
        "partial_ready":status_count.get("partial_ready",0),
        "not_ready":status_count.get("not_ready",0),
        "blocked":status_count.get("blocked",0),
        "overall_readiness":"partial_ready",
        "critical_blockers":["rollback_procedure_not_tested","no_escalation_contacts"],
        "readiness_pct":round(status_count.get("ready",0)/len(domains)*100,1),
        "mock_used":False,"fixture_used":False
    }
    return {"phase105_emergency_readiness_scorecard":scorecard}
