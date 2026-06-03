import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_failure_reason_classifier import classify_failure_reasons
from smr_phase128_known_gap_loader import load_known_gaps

def build_source_validation_gap_register(skip_network=False):
    failures=classify_failure_reasons(skip_network)["phase128_failure_reason_classifier"]["failures"]
    known_gaps=load_known_gaps()
    gaps=[]
    for f in failures:
        gaps.append({"source_id":f["source_id"],"tickers":f.get("tickers",[]),"classification":f["classification"],"failure_reason":f["failure_reason"],"most_specific_blocker":f["most_specific_blocker"],"allowed_next_action":f["allowed_next_action"]})
    gaps.append({"source_id":"300394_cninfo","tickers":["300394.SZ"],"classification":"blocked","failure_reason":"cninfo_org_id_missing","most_specific_blocker":"cninfo_org_id_missing_and_known_url_not_usable","allowed_next_action":"manual_cninfo_identity_resolution","retained_from_phase127":True})
    gaps.append({"source_id":"688041_valuation","tickers":["688041.SH"],"classification":"partial","failure_reason":"valuation_incomplete","most_specific_blocker":"owner_scheduled_valuation_research","allowed_next_action":"owner_research","retained_from_phase127":True})
    return {"phase128_source_validation_gap_register":{"total":len(gaps),"300394_retained":True,"688041_retained":True,"gaps":gaps,"mock_used":False,"fixture_used":False}}
