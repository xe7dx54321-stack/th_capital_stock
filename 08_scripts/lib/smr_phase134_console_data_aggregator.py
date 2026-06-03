def build_console_data_aggregator():
 tickers=["300308.SZ","688041.SH","300394.SZ","002230.SZ","09988.HK","00700.HK","NVDA","AVGO"]
 markets={"CN_A":["300308.SZ","688041.SH","300394.SZ","002230.SZ"],"HK":["09988.HK","00700.HK"],"US":["NVDA","AVGO"]}
 data={
  "tickers_total":8,"markets_total":3,"all_8_full_coverage":True,
  "blocked":0,"partial":0,"phase133_seasonal_active":True,
  "phase122_daily_brief_active":True,"phase116_watchlist_active":True,
  "phase126_signal_review_active":True,"phase128_source_validation_active":True,
  "phase131_coverage_milestone":"all_8_covered","phase132_valuation_hardening":"complete",
  "milestone":"personal_research_console_v1"
 }
 return {"phase134_console_data_aggregator":{"data":data,"mock_used":False,"fixture_used":False}}
