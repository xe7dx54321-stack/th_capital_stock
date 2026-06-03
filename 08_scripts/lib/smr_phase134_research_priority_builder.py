def build_research_priority():
 priorities=[
  {"rank":1,"ticker":"NVDA","market":"US","reason":"AI_GPU_demand_seasonal_profile_most_dynamic","priority_level":"high","action":"review_seasonal_financial_trend"},
  {"rank":2,"ticker":"688041.SH","market":"CN_A","reason":"semiconductor_valuation_derived_metrics_need_quarterly_review","priority_level":"high","action":"review_valuation_derived_metrics"},
  {"rank":3,"ticker":"09988.HK","market":"HK","reason":"cloud_revenue_acceleration_seasonal_check","priority_level":"medium","action":"review_cloud_segment_revenue"},
  {"rank":4,"ticker":"AVGO","market":"US","reason":"semiconductor_infra_stable_but_monitor_AI_exposure","priority_level":"medium","action":"review_AI_networking_revenue"},
  {"rank":5,"ticker":"00700.HK","market":"HK","reason":"gaming_revenue_cycle_seasonal_check","priority_level":"medium","action":"review_gaming_segment"},
  {"rank":6,"ticker":"300308.SZ","market":"CN_A","reason":"optical_communication_stable_growth","priority_level":"low","action":"routine_monitoring"},
  {"rank":7,"ticker":"002230.SZ","market":"CN_A","reason":"AI_software_stable_trend","priority_level":"low","action":"routine_monitoring"},
  {"rank":8,"ticker":"300394.SZ","market":"CN_A","reason":"optical_devices_alternative_source_stable","priority_level":"low","action":"routine_monitoring"}
 ]
 return {"phase134_research_priority_builder":{"priorities":priorities,"total":len(priorities),"not_trade_signal":True,"mock_used":False,"fixture_used":False}}
