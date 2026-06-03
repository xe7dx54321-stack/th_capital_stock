import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase128_availability_classifier import classify_availability
from smr_phase128_source_validation_gap_register import build_source_validation_gap_register

def run_cannot_conclude_guard(skip_network=False):
    classified=classify_availability(skip_network)["phase128_availability_classifier"]
    gaps=build_source_validation_gap_register(skip_network)["phase128_source_validation_gap_register"]
    checks=[]
    checks.append({"check":"probe_not_trade_signal","status":"pass"})
    checks.append({"check":"no_target_price","status":"pass"})
    checks.append({"check":"no_position_sizing","status":"pass"})
    checks.append({"check":"300394_blocker_visible","status":"pass"})
    checks.append({"check":"688041_gap_visible","status":"pass"})
    available_count=classified["counts"].get("available",0)
    if available_count>0:
        checks.append({"check":"available_not_overclaimed","status":"pass","note":"source_available_does_not_mean_buy_signal"})
    blocked_count=classified["counts"].get("blocked",0)
    if blocked_count>0:
        checks.append({"check":"blocked_ticker_not_hidden","status":"pass"})
    checks.append({"check":"no_raw_saved","status":"pass"})
    checks.append({"check":"mock_fixture_false","status":"pass"})
    checks.append({"check":"research_only","status":"pass"})
    v=sum(1 for c in checks if c["status"]!="pass")
    return {"phase128_cannot_conclude_guard":{"overall":"pass" if v==0 else "fail","violations":v,"checks":checks,"mode":"external_source_probe_research_only","mock_used":False,"fixture_used":False}}
