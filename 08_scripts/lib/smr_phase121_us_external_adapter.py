def build_us_external_adapter():
 t=[
  {"ticker":"NVDA","existing":["yfinance"],"candidates":["sec_edgar","sec_10k","sec_10q","sec_8k","finviz","marketwatch","fool_earnings"],"before":1,"after":8,"financial":"available","probe_required":True},
  {"ticker":"AVGO","existing":["yfinance"],"candidates":["sec_edgar","sec_10k","sec_10q","sec_8k","finviz","marketwatch","fool_earnings"],"before":1,"after":8,"financial":"available","probe_required":True},
 ]
 return {"phase121_us_external_adapter":{"total":len(t),"source_count_before":1,"source_count_after_candidate":8,"tickers":t,"mock_used":False,"fixture_used":False}}
