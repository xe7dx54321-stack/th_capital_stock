def build_hk_external_adapter():
 t=[
  {"ticker":"09988.HK","existing":["yfinance","akshare_hk"],"candidates":["hkex_news","hkex_filing","aastocks","futu_public"],"before":2,"after":6,"financial":"available","probe_required":True},
  {"ticker":"00700.HK","existing":["yfinance","akshare_hk"],"candidates":["hkex_news","hkex_filing","aastocks","futu_public"],"before":2,"after":6,"financial":"available","probe_required":True},
 ]
 return {"phase121_hk_external_adapter":{"total":len(t),"source_count_before":2,"source_count_after_candidate":6,"tickers":t,"mock_used":False,"fixture_used":False}}
