def build_thesis_confidence_scorer():
 scores=[
  {"ticker":"NVDA","thesis_id":"TH-NVDA-001","confidence":"high","score":85,"drivers":["direct_financial_observation","active_catalyst","owner_feedback_confirming"],"limiters":["SEC_direct_access_limitation"]},
  {"ticker":"688041.SH","thesis_id":"TH-688041-001","confidence":"medium","score":65,"drivers":["financial_data_confirmed","policy_catalyst_active"],"limiters":["valuation_derived_estimates","peer_data_limited"]},
  {"ticker":"300394.SZ","thesis_id":"TH-300394-001","confidence":"low","score":35,"drivers":["eastmoney_alternative_usable"],"limiters":["cninfo_org_id_missing","no_direct_comparison_possible"]}
 ]
 return {"phase138_thesis_confidence_scorer":{"scores":scores,"total":len(scores),"all_not_trade":True,"mock_used":False,"fixture_used":False}}
