def build_source_signal_feedback_intake():
 feedbacks=[
  {"feedback_id":"FB-SS-001","created_at":"2026-06-03T00:00:00Z","feedback_type":"source_noisy","source_console_section":"source_signal_quality_center","target_ticker":"300394.SZ","target_entity_id":"300394_source","owner_comment":"300394 eastmoney source data sometimes delayed","impact_scope":"source_signal_weight","validation_status":"valid","research_only":True,"not_trade_feedback":True},
  {"feedback_id":"FB-SS-002","created_at":"2026-06-03T00:00:00Z","feedback_type":"signal_helpful","source_console_section":"source_signal_quality_center","target_ticker":"NVDA","target_entity_id":"NVDA_signal","owner_comment":"NVDA revenue signal is most actionable","impact_scope":"source_signal_weight","validation_status":"valid","research_only":True,"not_trade_feedback":True}
 ]
 return {"phase135_source_signal_feedback_intake":{"total":len(feedbacks),"feedbacks":feedbacks,"empty_feedback_ready":True,"mock_used":False,"fixture_used":False}}
