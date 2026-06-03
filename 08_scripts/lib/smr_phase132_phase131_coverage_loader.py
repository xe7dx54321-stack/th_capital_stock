import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase131_watchlist_coverage_update import build_watchlist_coverage_update
def load_phase131_coverage():
 coverage=build_watchlist_coverage_update()["phase131_watchlist_coverage_update"]
 return {"phase132_phase131_coverage_loader":{"coverage":coverage,"688041_status":"partial_valuation_incomplete","remaining_gap":"valuation_metrics","mock_used":False,"fixture_used":False}}
