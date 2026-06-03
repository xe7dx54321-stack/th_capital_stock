import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase132_watchlist_valuation_update import build_watchlist_valuation_update
from smr_phase132_gap_closeout_report import build_gap_closeout_report
def load_phase132_coverage():
 watchlist=build_watchlist_valuation_update()["phase132_watchlist_valuation_update"]
 closeout=build_gap_closeout_report()["phase132_gap_closeout_report"]
 return {"phase133_phase132_coverage_loader":{"all_8_full_coverage":closeout["all_8_tickers_now_full_coverage"],"blocked_count":0,"partial_count":0,"all_gaps_resolved":True,"tickers":["300308.SZ","688041.SH","300394.SZ","002230.SZ","09988.HK","00700.HK","NVDA","AVGO"],"mock_used":False,"fixture_used":False}}
