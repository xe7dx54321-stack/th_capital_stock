import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase130_disclosure_coverage_classifier import classify_disclosure_coverage

def build_watchlist_status_update():
    coverage=classify_disclosure_coverage()["phase130_disclosure_coverage_classifier"]
    return {"phase130_watchlist_status_update":{"ticker":"300394.SZ","previous_watchlist_status":"blocked","new_watchlist_status":"alternative_source_mapped_awaiting_owner_verification","blocker_resolution_progress":"source_identified_not_yet_integrated","quant_monitoring_status":"pending_alternative_source_integration","financial_data_source_ready":coverage["financial_data_feasible"],"priority":"high_if_owner_wants_300394_in_coverage","pending_created":0,"paper_order_created":0,"real_trade_created":0,"mock_used":False,"fixture_used":False}}
