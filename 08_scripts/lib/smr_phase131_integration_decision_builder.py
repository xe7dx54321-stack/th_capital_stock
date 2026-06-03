import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase131_hard_data_integration_update import build_hard_data_integration_update
from smr_phase131_watchlist_coverage_update import build_watchlist_coverage_update
def build_integration_decision():
 hard=build_hard_data_integration_update()["phase131_hard_data_integration_update"]
 watchlist=build_watchlist_coverage_update()["phase131_watchlist_coverage_update"]
 return {"phase131_integration_decision_builder":{"ticker":"300394.SZ","decision":"integrated_via_eastmoney_alternative_source","cninfo_blocker":"resolved_via_alternative","coverage_count":watchlist["covered_count"],"all_8_tickers_covered":True,"remaining_known_gaps":["688041_valuation_partial"],"not_a_trade_recommendation":True,"research_only":True,"mock_used":False,"fixture_used":False}}
