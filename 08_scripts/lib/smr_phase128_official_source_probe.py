import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_source_request_adapter import probe_url
from smr_phase128_probe_target_planner import plan_probe_targets

def probe_official_sources(skip_network=False):
    targets=plan_probe_targets()["phase128_probe_target_planner"]["targets"]
    official=[t for t in targets if t.get("category")=="official"]
    results=[]
    for t in official:
        r={"source_id":t["source_id"],"type":t["type"],"market":t["market"],"tickers":t["tickers"]}
        if skip_network:
            r["probe_status"]="skipped"
            r["reachable"]=False
            r["note"]="skip_network_mode"
        else:
            pr=probe_url(t["probe_url"],t.get("method","HEAD"))
            r["probe_status"]=pr["status"]
            r["reachable"]=pr["reachable"]
            r["http_code"]=pr["http_code"]
            if pr["error"]: r["error"]=pr["error"]
        results.append(r)
    available=sum(1 for r in results if r.get("probe_status")=="available")
    blocked=sum(1 for r in results if r.get("probe_status")=="blocked")
    skipped=sum(1 for r in results if r.get("probe_status")=="skipped")
    return {"phase128_official_source_probe":{"total":len(results),"available":available,"blocked":blocked,"skipped":skipped,"results":results,"mock_used":False,"fixture_used":False,"raw_saved":False}}
