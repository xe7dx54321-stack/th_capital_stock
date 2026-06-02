def build_taxonomy():
 types=["evidence_confirmed","evidence_weakened","catalyst_realized","catalyst_failed","risk_materialized","risk_dissolved","signal_accurate","signal_noise","source_refreshed","source_stale","deep_dive_completed","decision_reversed"]
 return {"phase125_taxonomy":{"total":len(types),"types":types,"no_financial_types":True,"no_profit_loss":True,"no_return":True,"mock_used":False,"fixture_used":False}}
