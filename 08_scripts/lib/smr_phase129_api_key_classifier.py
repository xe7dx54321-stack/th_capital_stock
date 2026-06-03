import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase129_fallback_probe_executor import execute_fallback_probe

def classify_api_key_required(skip_network=False):
    results=execute_fallback_probe(skip_network)["phase129_fallback_probe_executor"]["results"]
    classified=[]
    for r in results:
        c={"source_id":r["source_id"],"requires_api_key":False,"api_key_provider":"N/A","api_key_status":"not_required"}
        if r["source_id"]=="transcript_guidance_manual":
            c["requires_api_key"]=True
            c["api_key_provider"]="Seeking Alpha / Motley Fool / Alpha Vantage"
            c["api_key_status"]="optional_paid_tier"
            c["free_tier_available"]=True
            c["free_tier_limitation"]="limited transcript access"
        classified.append(c)
    needs_key=sum(1 for c in classified if c["requires_api_key"])
    return {"phase129_api_key_classifier":{"total":len(classified),"api_key_required":needs_key,"free_fallback_available":len(classified)-needs_key,"results":classified,"mock_used":False,"fixture_used":False}}
