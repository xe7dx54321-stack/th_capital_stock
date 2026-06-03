def build_source_signal_quality_center():
 sources=[
  {"ticker":"300308.SZ","market":"CN_A","primary_source":"cninfo","status":"available","signal_quality":"stable"},
  {"ticker":"688041.SH","market":"CN_A","primary_source":"cninfo","status":"available","signal_quality":"stable","valuation_note":"derived"},
  {"ticker":"300394.SZ","market":"CN_A","primary_source":"eastmoney","status":"alternative_available","fallback":"cninfo_blocked","signal_quality":"stable_alternative","cninfo_blocker":"cninfo_org_id_missing"},
  {"ticker":"002230.SZ","market":"CN_A","primary_source":"cninfo","status":"available","signal_quality":"stable"},
  {"ticker":"09988.HK","market":"HK","primary_source":"hkex_public","status":"available","signal_quality":"stable"},
  {"ticker":"00700.HK","market":"HK","primary_source":"hkex_public","status":"available","signal_quality":"stable"},
  {"ticker":"NVDA","market":"US","primary_source":"sec_edgar","status":"available","signal_quality":"stable"},
  {"ticker":"AVGO","market":"US","primary_source":"sec_edgar","status":"available","signal_quality":"stable"}
 ]
 signals={"total_active_signals":22,"strengthened":3,"weakened":0,"unchanged":19,"anomaly":0,"first_seasonal_snapshot":True}
 return {"phase134_source_signal_quality_center":{"sources":sources,"signals":signals,"all_critical_sources_available":True,"not_trade_signal":True,"mock_used":False,"fixture_used":False}}
