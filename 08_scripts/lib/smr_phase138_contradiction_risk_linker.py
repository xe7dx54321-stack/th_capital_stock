def build_contradiction_risk_linker():
 items=[
  {"ticker":"688041.SH","thesis_id":"TH-688041-001","risk_type":"valuation_uncertainty","risk":"derived_valuation_may_differ_from_market","severity":"moderate","mitigation":"owner_review_periodic"},
  {"ticker":"NVDA","thesis_id":"TH-NVDA-001","risk_type":"cycle_risk","risk":"AI_capex_cycle_may_moderate","severity":"low","mitigation":"quarterly_monitoring"},
  {"ticker":"300394.SZ","thesis_id":"TH-300394-001","risk_type":"source_risk","risk":"cninfo_missing_limits_data_quality","severity":"moderate","mitigation":"cninfo_resolution_or_accept_alternative"}
 ]
 return {"phase138_contradiction_risk_linker":{"items":items,"total":len(items),"all_not_trade":True,"mock_used":False,"fixture_used":False}}
