import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase129_fallback_probe_executor import execute_fallback_probe
from smr_phase129_gap_register import build_gap_register

def build_fallback_board(skip_network=False):
    probe=execute_fallback_probe(skip_network)["phase129_fallback_probe_executor"]
    gaps=build_gap_register(skip_network)["phase129_gap_register"]
    sections={"resolved_via_fallback":[],"manual_workflow_required":[],"retained_blockers":[]}
    for r in probe["results"]:
        if r.get("resolution")=="third_party_equivalent_available":
            sections["resolved_via_fallback"].append(r)
        elif r.get("resolution")=="manual_source_workflow_required":
            sections["manual_workflow_required"].append(r)
    for g in gaps["gaps"]:
        if g.get("retained_from_phase128"):
            sections["retained_blockers"].append(g)
    return {"phase129_fallback_board":{"sources_total":probe["total"],"resolved":probe["available"],"manual_required":probe["manual_required"],"blockers_retained":len(sections["retained_blockers"]),"sections":sections,"not_trade_board":True,"mock_used":False,"fixture_used":False}}
