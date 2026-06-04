# Phase174 daily monitoring plan
from smr_phase174_coverage_state_registry import build_coverage_state_registry

def build_daily_monitoring_plan():
    registry = build_coverage_state_registry()
    r = registry["phase174_coverage_state_registry"]
    daily_entries = [e for e in r["entries"] if e["daily_monitoring_eligible"]]
    plans = []
    for e in daily_entries:
        plans.append({
            "candidate_id":e["candidate_id"],
            "frequency":"daily",
            "check_items":["financial_signal_check","delta_detection","anomaly_scan"],
            "output_target":"portfolio_watch_board",
            "cannot_conclude":["daily_check_is_not_trade_signal","monitoring_not_recommendation"]
        })
    return {"phase174_daily_monitoring_plan":{
        "daily_monitoring_enabled":True,
        "eligible_candidates":len(daily_entries),
        "plans":plans,
        "monitoring_not_trade":True,
        "mock_used":False,"fixture_used":False
    }}
