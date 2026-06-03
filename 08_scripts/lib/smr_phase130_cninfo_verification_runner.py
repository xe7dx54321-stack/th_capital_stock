import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase130_cninfo_candidate_registry import build_cninfo_candidate_registry

def run_cninfo_verification(skip_network=False):
    candidates=build_cninfo_candidate_registry()["phase130_cninfo_candidate_registry"]["candidates"]
    results=[]
    for c in candidates:
        r={"candidate_id":c["candidate_id"],"search_method":c["search_method"],"status":c["status"]}
        if skip_network:
            r["verification_status"]="skipped"
            r["org_id_found"]=False
        elif c["status"]=="verifiable":
            r["verification_status"]="url_constructed_not_probed"
            r["org_id_found"]=False
            r["note"]="verifiable URL exists but org_id still not confirmed without browser probe"
        elif c["status"]=="manual_required":
            r["verification_status"]="manual_required"
            r["org_id_found"]=False
            r["note"]="requires manual CNINFO website search"
        else:
            r["verification_status"]="unverified"
            r["org_id_found"]=False
            r["note"]="requires CNINFO API or manual search"
        results.append(r)
    org_found=any(r.get("org_id_found") for r in results)
    return {"phase130_cninfo_verification_runner":{"total":len(results),"org_id_confirmed":org_found,"results":results,"conclusion":"org_id_still_not_confirmed_without_manual_api_or_browser","mock_used":False,"fixture_used":False,"browser_used":False}}
