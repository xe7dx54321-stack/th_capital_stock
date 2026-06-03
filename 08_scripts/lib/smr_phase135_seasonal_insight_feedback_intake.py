def build_seasonal_insight_feedback_intake():
 feedbacks=[
  {"feedback_id":"FB-SI-001","created_at":"2026-06-03T00:00:00Z","feedback_type":"ticker_card_useful","source_console_section":"seasonal_insight_center","target_ticker":"ALL","target_entity_id":"seasonal_insight","owner_comment":"Seasonal insight helpful for understanding quarterly patterns","impact_scope":"brief_layout","validation_status":"valid","research_only":True,"not_trade_feedback":True}
 ]
 return {"phase135_seasonal_insight_feedback_intake":{"total":len(feedbacks),"feedbacks":feedbacks,"empty_feedback_ready":True,"mock_used":False,"fixture_used":False}}
