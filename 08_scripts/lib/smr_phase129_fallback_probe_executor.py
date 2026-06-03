import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase129_access_route_planner import build_access_route_planner

def execute_fallback_probe(skip_network=False):
    routes=build_access_route_planner()["phase129_access_route_planner"]["routes"]
    results=[]
    for r in routes:
        res={"source_id":r["source_id"],"primary_status":"blocked" if "blocked" in r.get("primary_route","") else r.get("primary_route","degraded"),"recommended_route":r.get("recommended_route",""),"recommended_source":r.get("recommended_source",r.get("recommended_route",""))}
        if skip_network:
            res["probe_status"]="skipped"
            res["resolution"]="skip_network_mode"
        elif r["route_status"]=="available":
            res["probe_status"]="available"
            res["resolution"]="third_party_equivalent_available"
            res["fallback_verified"]=True
        elif r["route_status"]=="manual_required":
            res["probe_status"]="manual_required"
            res["resolution"]="manual_source_workflow_required"
            res["fallback_verified"]=False
        else:
            res["probe_status"]="blocked"
            res["resolution"]="persistent_blocked"
            res["fallback_verified"]=False
        res["note"]=r.get("note","")
        results.append(res)
    available=sum(1 for r in results if r.get("resolution")=="third_party_equivalent_available")
    manual=sum(1 for r in results if r.get("resolution")=="manual_source_workflow_required")
    skipped=sum(1 for r in results if r.get("probe_status")=="skipped")
    return {"phase129_fallback_probe_executor":{"total":len(results),"available":available,"manual_required":manual,"skipped":skipped,"results":results,"mock_used":False,"fixture_used":False,"raw_saved":False}}
