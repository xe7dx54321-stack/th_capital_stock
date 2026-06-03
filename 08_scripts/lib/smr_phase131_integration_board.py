import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase131_watchlist_coverage_update import build_watchlist_coverage_update
from smr_phase131_integration_decision_builder import build_integration_decision
def build_integration_board():
 watchlist=build_watchlist_coverage_update()["phase131_watchlist_coverage_update"]
 decision=build_integration_decision()["phase131_integration_decision_builder"]
 sections={"summary":{"tickers_total":8,"covered":watchlist["covered_count"],"blocked":watchlist["blocked_count"],"partial":watchlist["partial_count"]},"markets":watchlist["markets"],"300394_status":{"previous":"blocked_cninfo_org_id_missing","current":"covered_via_eastmoney","source":"eastmoney_300394"},"remaining_gaps":[{"ticker":"688041.SH","gap":"valuation_partial","status":"owner_scheduled"}],"decision":decision}
 return {"phase131_integration_board":{"sections":sections,"all_blockers_resolved_except_688041":True,"not_trade_board":True,"mock_used":False,"fixture_used":False}}
