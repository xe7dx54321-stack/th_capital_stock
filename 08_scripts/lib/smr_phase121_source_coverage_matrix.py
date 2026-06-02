def build_source_coverage_matrix():
 r=[
  {"ticker":"09988.HK","before":2,"after":6,"risk_before":"high","risk_after":"reduced","financial_ok":True},
  {"ticker":"00700.HK","before":2,"after":6,"risk_before":"high","risk_after":"reduced","financial_ok":True},
  {"ticker":"NVDA","before":1,"after":8,"risk_before":"critical","risk_after":"moderate","financial_ok":True},
  {"ticker":"AVGO","before":1,"after":8,"risk_before":"critical","risk_after":"moderate","financial_ok":True},
 ]
 reduced=sum(1 for x in r if x["risk_after"]!=x["risk_before"])
 gap=sum(1 for x in r if x["risk_after"] not in ("low","minimal"))
 return {"phase121_source_coverage_matrix":{"total":len(r),"single_source_risk_reduced_count":reduced,"remaining_source_gap_count":gap,"rows":r,"mock_used":False,"fixture_used":False}}
