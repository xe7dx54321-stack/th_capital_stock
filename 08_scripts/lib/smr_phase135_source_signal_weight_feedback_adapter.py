def build_source_signal_weight_feedback_adapter():
 adjustments=[
  {"from_feedback":"FB-SS-001","ticker":"300394.SZ","source":"eastmoney","weight_before":"standard","weight_after":"reduced","reason":"Owner flags eastmoney source as sometimes noisy"},
  {"from_feedback":"FB-SS-002","ticker":"NVDA","signal":"revenue","weight_before":"standard","weight_after":"elevated","reason":"Owner finds NVDA revenue signal most actionable"}
 ]
 return {"phase135_source_signal_weight_feedback_adapter":{"adjustments":adjustments,"total_adjusted":len(adjustments),"not_trade_signal":True,"mock_used":False,"fixture_used":False}}
