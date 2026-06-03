def build_ticker_card_feedback_intake():
 feedbacks=[
  {"feedback_id":"FB-TC-001","created_at":"2026-06-03T00:00:00Z","feedback_type":"ticker_card_useful","source_console_section":"ticker_cards","target_ticker":"NVDA","target_entity_id":"NVDA_card","owner_comment":"NVDA card most useful for AI capex tracking","impact_scope":"research_priority","validation_status":"valid","research_only":True,"not_trade_feedback":True},
  {"feedback_id":"FB-TC-002","created_at":"2026-06-03T00:00:00Z","feedback_type":"raise_research_attention","source_console_section":"ticker_cards","target_ticker":"688041.SH","target_entity_id":"688041_card","owner_comment":"688041 valuation derived metrics need closer watch","impact_scope":"research_priority","validation_status":"valid","research_only":True,"not_trade_feedback":True}
 ]
 return {"phase135_ticker_card_feedback_intake":{"total":len(feedbacks),"feedbacks":feedbacks,"empty_feedback_ready":True,"mock_used":False,"fixture_used":False}}
