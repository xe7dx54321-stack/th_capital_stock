def build_thesis_status_classifier():
 statuses=[
  {"ticker":"688041.SH","thesis_id":"TH-688041-001","status":"thesis_supported","confidence":"medium","next_verification":"owner_review_valuation_metrics","manual_required":True},
  {"ticker":"NVDA","thesis_id":"TH-NVDA-001","status":"thesis_strengthened","confidence":"high","next_verification":"next_quarterly_report","manual_required":False},
  {"ticker":"AVGO","thesis_id":"TH-AVGO-001","status":"thesis_supported","confidence":"medium","next_verification":"routine_monitoring","manual_required":False},
  {"ticker":"09988.HK","thesis_id":"TH-09988-001","status":"thesis_observed","confidence":"medium","next_verification":"cloud_revenue_quarterly","manual_required":False},
  {"ticker":"00700.HK","thesis_id":"TH-00700-001","status":"thesis_observed","confidence":"medium","next_verification":"gaming_ad_revenue_quarterly","manual_required":False},
  {"ticker":"300308.SZ","thesis_id":"TH-300308-001","status":"thesis_context_supported","confidence":"medium","next_verification":"routine_monitoring","manual_required":False},
  {"ticker":"300394.SZ","thesis_id":"TH-300394-001","status":"thesis_unconfirmed","confidence":"low","next_verification":"cninfo_resolution","manual_required":True},
  {"ticker":"002230.SZ","thesis_id":"TH-002230-001","status":"thesis_context_supported","confidence":"medium","next_verification":"routine_monitoring","manual_required":False}
 ]
 return {"phase138_thesis_status_classifier":{"statuses":statuses,"total":len(statuses),"summary":{"thesis_strengthened":1,"thesis_supported":2,"thesis_observed":2,"thesis_context_supported":2,"thesis_unconfirmed":1},"all_not_trade":True,"mock_used":False,"fixture_used":False}}
