import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase129_fallback_probe_executor import execute_fallback_probe

def classify_proxy_required(skip_network=False):
    results=execute_fallback_probe(skip_network)["phase129_fallback_probe_executor"]["results"]
    classified=[]
    for r in results:
        c={"source_id":r["source_id"],"requires_proxy":False,"proxy_reason":"N/A"}
        if r["resolution"]=="third_party_equivalent_available":
            c["requires_proxy"]=False
            c["proxy_reason"]="third_party_equivalent_no_proxy_needed"
            c["recommendation"]="use_third_party_equivalent_directly"
        elif r["resolution"]=="persistent_blocked":
            c["requires_proxy"]=True
            c["proxy_reason"]="cn_network_restriction_on_official_source"
            c["recommendation"]="third_party_equivalent_preferred_over_proxy"
        classified.append(c)
    needs_proxy=sum(1 for c in classified if c["requires_proxy"])
    return {"phase129_proxy_classifier":{"total":len(classified),"proxy_required":needs_proxy,"proxy_avoided_by_fallback":len(classified)-needs_proxy,"results":classified,"mock_used":False,"fixture_used":False}}
