import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_availability_classifier import classify_availability
from smr_phase128_pending_source_loader import load_pending_sources

def build_pending_network_closeout(skip_network=False):
    pending_before=load_pending_sources()["phase128_pending_source_loader"]["total"]
    classified=classify_availability(skip_network)["phase128_availability_classifier"]
    counts=classified["counts"]
    resolved=counts.get("available",0)
    still_blocked=counts.get("blocked",0)+counts.get("unsupported",0)+counts.get("degraded_with_reason",0)
    manual=counts.get("manual_required",0)
    pending_after=still_blocked+manual
    return {"phase128_pending_network_closeout":{"pending_network_before":pending_before,"pending_network_after":pending_after,"resolved_to_available":resolved,"still_blocked":still_blocked,"manual_required":manual,"skipped":counts.get("skipped",0),"status":"probe_complete","mock_used":False,"fixture_used":False}}
