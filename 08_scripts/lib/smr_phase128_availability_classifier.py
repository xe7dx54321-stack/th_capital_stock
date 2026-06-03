import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_probe_result_normalizer import normalize_probe_results

def classify_availability(skip_network=False):
    norm=normalize_probe_results(skip_network)["phase128_probe_result_normalizer"]["results"]
    classified=[]
    for n in norm:
        c={"source_id":n["source_id"],"market":n["market"],"tickers":n["tickers"]}
        status=n["probe_status"]
        if status=="available": c["classification"]="available"
        elif status=="blocked":
            if n.get("http_code") in [401,403]: c["classification"]="blocked"
            elif n.get("http_code")==404: c["classification"]="unsupported"
            elif n.get("http_code") and n["http_code"]>=500: c["classification"]="degraded_with_reason"
            else: c["classification"]="blocked"
        elif status=="manual_required": c["classification"]="manual_required"
        elif status=="skipped": c["classification"]="skipped"
        else: c["classification"]="unknown"
        c["probe_status"]=status
        c["error"]=n.get("error")
        c["note"]=n.get("note","")
        classified.append(c)
    counts={"available":0,"metadata_only":0,"blocked":0,"manual_required":0,"api_key_required":0,"unsupported":0,"degraded_with_reason":0,"skipped":0}
    for c in classified: counts[c["classification"]]=counts.get(c["classification"],0)+1
    return {"phase128_availability_classifier":{"total":len(classified),"counts":counts,"results":classified,"mock_used":False,"fixture_used":False}}
