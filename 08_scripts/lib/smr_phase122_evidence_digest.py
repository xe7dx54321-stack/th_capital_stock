def build_evidence_digest():
 rows=[
  {"source_type":"financial","tickers":["NVDA","AVGO","09988.HK","00700.HK","300308.SZ","002230.SZ","688041.SH"],"status":"integrated","currency_boundary":"HKD_USD_CNY_separated"},
  {"source_type":"catalyst","tickers":["NVDA"],"status":"active_signal","note":"confirmed_inflection"},
  {"source_type":"watchlist","tickers":["09988.HK","00700.HK","NVDA","AVGO","300308.SZ","688041.SH","002230.SZ"],"status":"integrated"},
  {"source_type":"opportunity_monitor","tickers":[],"status":"monitoring"},
  {"source_type":"external_news","sources_pending":12,"available":2,"status":"partially_integrated","limit":"network_probe_required"},
 ]
 return {"phase122_evidence_digest":{"total_sources":len(rows),"integrated":4,"partially_integrated":1,"rows":rows,"research_only":True,"mock_used":False,"fixture_used":False}}
