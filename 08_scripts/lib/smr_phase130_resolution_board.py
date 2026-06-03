import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase130_gap_closeout_report import build_gap_closeout_report
from smr_phase130_disclosure_coverage_classifier import classify_disclosure_coverage
from smr_phase130_resolution_decision_report import build_resolution_decision_report

def build_resolution_board():
    closeout=build_gap_closeout_report()["phase130_gap_closeout_report"]
    coverage=classify_disclosure_coverage()["phase130_disclosure_coverage_classifier"]
    decision=build_resolution_decision_report()["phase130_resolution_decision_report"]
    sections={"resolution_status":{"blocker":closeout["original_blocker"],"status":closeout["blocker_status"],"cninfo_org_id":"still_missing"},"coverage_assessment":{"level":coverage["coverage_level"],"financial_data_feasible":coverage["financial_data_feasible"],"preferred_source":"eastmoney_300394"},"decision":decision,"owner_actions_required":True}
    return {"phase130_resolution_board":{"ticker":"300394.SZ","sections":sections,"not_trade_board":True,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"mock_used":False,"fixture_used":False}}
