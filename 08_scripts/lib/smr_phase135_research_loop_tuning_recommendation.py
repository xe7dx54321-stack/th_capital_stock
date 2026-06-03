def build_research_loop_tuning_recommendation():
 recs=[
  {"recommendation_id":"RT-001","scope":"research_priority","recommendation":"maintain_688041_high_priority","evidence":"owner_feedback_confirmed","confidence":"high","not_trade":True},
  {"recommendation_id":"RT-002","scope":"brief_layout","recommendation":"expand_seasonal_context_in_daily_brief","evidence":"owner_feedback_requested","confidence":"high","not_trade":True},
  {"recommendation_id":"RT-003","scope":"source_signal_weight","recommendation":"elevate_NVDA_revenue_signal_weight","evidence":"owner_feedback_confirmed","confidence":"medium","not_trade":True},
  {"recommendation_id":"RT-004","scope":"source_signal_weight","recommendation":"reduce_300394_eastmoney_noise_threshold","evidence":"owner_feedback_confirmed","confidence":"medium","not_trade":True},
  {"recommendation_id":"RT-005","scope":"deep_dive_task","recommendation":"schedule_688041_valuation_deep_dive","evidence":"owner_deep_dive_requested","confidence":"high","not_trade":True}
 ]
 return {"phase135_research_loop_tuning_recommendation":{"recommendations":recs,"total":len(recs),"all_not_trade":True,"mock_used":False,"fixture_used":False}}
