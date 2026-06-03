import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_availability_classifier import classify_availability

def classify_failure_reasons(skip_network=False):
    classified=classify_availability(skip_network)["phase128_availability_classifier"]["results"]
    failures=[c for c in classified if c["classification"] not in ["available","skipped"]]
    for f in failures:
        if f["classification"]=="manual_required": f["failure_reason"]="requires_manual_aggregation_or_paid_service"
        elif f.get("http_code") in [401,403]: f["failure_reason"]="access_denied_authentication_required"
        elif f.get("http_code")==404: f["failure_reason"]="endpoint_not_found"
        elif f.get("http_code") and f["http_code"]>=500: f["failure_reason"]="server_error_degraded"
        elif f.get("error") and "timeout" in str(f.get("error","")).lower(): f["failure_reason"]="connection_timeout"
        elif f.get("error") and "dns" in str(f.get("error","")).lower(): f["failure_reason"]="dns_resolution_failure"
        else: f["failure_reason"]="network_unreachable_or_blocked"
        f["most_specific_blocker"]=f["failure_reason"]
        f["allowed_next_action"]="retry_with_different_network_or_alternative_source" if f["classification"]=="blocked" else "manual_intervention_required"
    return {"phase128_failure_reason_classifier":{"total_failures":len(failures),"failures":failures,"mock_used":False,"fixture_used":False}}
