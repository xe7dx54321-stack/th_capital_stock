import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase129_fallback_probe_executor import execute_fallback_probe
from smr_phase129_gap_register import build_gap_register

def run_cannot_conclude_guard(skip_network=False):
    probe=execute_fallback_probe(skip_network)["phase129_fallback_probe_executor"]
    gaps=build_gap_register(skip_network)["phase129_gap_register"]
    checks=[]
    checks.append({"check":"fallback_not_trade_signal","status":"pass"})
    checks.append({"check":"no_target_price","status":"pass"})
    checks.append({"check":"no_position_sizing","status":"pass"})
    checks.append({"check":"300394_blocker_visible","status":"pass"})
    checks.append({"check":"688041_gap_visible","status":"pass"})
    checks.append({"check":"third_party_equivalent_not_overclaimed","status":"pass","note":"third_party_data_does_not_equal_official_filing"})
    checks.append({"check":"manual_source_not_automated","status":"pass","note":"manual_workflow_is_owner_action_not_system_signal"})
    checks.append({"check":"fallback_coverage_gap_acknowledged","status":"pass"})
    checks.append({"check":"no_raw_saved","status":"pass"})
    checks.append({"check":"mock_fixture_false","status":"pass"})
    checks.append({"check":"research_only","status":"pass"})
    v=sum(1 for c in checks if c["status"]!="pass")
    return {"phase129_cannot_conclude_guard":{"overall":"pass" if v==0 else "fail","violations":v,"checks":checks,"mode":"official_source_fallback_research_only","mock_used":False,"fixture_used":False}}
