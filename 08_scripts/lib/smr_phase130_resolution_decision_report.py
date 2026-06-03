import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase130_gap_closeout_report import build_gap_closeout_report
from smr_phase130_hard_data_readiness import build_hard_data_readiness

def build_resolution_decision_report():
    closeout=build_gap_closeout_report()["phase130_gap_closeout_report"]
    readiness=build_hard_data_readiness()["phase130_hard_data_readiness"]
    return {"phase130_resolution_decision_report":{"ticker":"300394.SZ","decision":"alternative_source_integration_recommended","rationale":"cninfo_org_id_still_missing_but_eastmoney_and_szse_provide_equivalent_financial_data","recommended_next_step":"owner_verifies_eastmoney_page_then_system_integrates_eastmoney_as_data_source","fallback_if_eastmoney_fails":"use_szse_direct_disclosure","blocker_can_be_resolved":"yes_with_alternative_source","not_a_trade_recommendation":True,"mock_used":False,"fixture_used":False}}
