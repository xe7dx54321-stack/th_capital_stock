def build_watchlist_status_center():
 statuses=[
  {"ticker":"NVDA","market":"US","watchlist_status":"continue_tracking","financial_signal":"strengthened","valuation_signal":"stable","priority":"high"},
  {"ticker":"AVGO","market":"US","watchlist_status":"continue_tracking","financial_signal":"unchanged","valuation_signal":"stable","priority":"medium"},
  {"ticker":"09988.HK","market":"HK","watchlist_status":"continue_tracking","financial_signal":"strengthened","valuation_signal":"stable","priority":"medium"},
  {"ticker":"00700.HK","market":"HK","watchlist_status":"continue_tracking","financial_signal":"unchanged","valuation_signal":"stable","priority":"medium"},
  {"ticker":"300308.SZ","market":"CN_A","watchlist_status":"continue_tracking","financial_signal":"unchanged","valuation_signal":"stable","priority":"low"},
  {"ticker":"688041.SH","market":"CN_A","watchlist_status":"continue_tracking","financial_signal":"unchanged","valuation_signal":"derived_monitor","priority":"high"},
  {"ticker":"300394.SZ","market":"CN_A","watchlist_status":"continue_tracking","financial_signal":"unchanged","valuation_signal":"stable","priority":"low","note":"alternative_source"},
  {"ticker":"002230.SZ","market":"CN_A","watchlist_status":"continue_tracking","financial_signal":"unchanged","valuation_signal":"stable","priority":"low"}
 ]
 return {"phase134_watchlist_status_center":{"total":len(statuses),"statuses":statuses,"not_trade_signal":True,"pending_created":0,"mock_used":False,"fixture_used":False}}
