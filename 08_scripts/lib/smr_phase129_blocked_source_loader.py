import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_availability_classifier import classify_availability
def load_blocked_sources():
 classified=classify_availability(skip_network=False)["phase128_availability_classifier"]["results"]
 blocked=[c for c in classified if c["classification"] in ["blocked","degraded_with_reason","manual_required"]]
 return {"phase129_blocked_source_loader":{"total":len(blocked),"blocked_sources":blocked,"source_ids":[b["source_id"] for b in blocked],"mock_used":False,"fixture_used":False}}
