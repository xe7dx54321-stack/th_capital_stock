def build_daily_brief_feedback_intake():
 feedbacks=[
  {"feedback_id":"FB-DB-001","created_at":"2026-06-03T00:00:00Z","feedback_type":"brief_too_shallow","source_console_section":"daily_brief_preview","target_ticker":"ALL","target_entity_id":"daily_brief","owner_comment":"Daily brief should include more seasonal context","impact_scope":"brief_layout","validation_status":"valid","research_only":True,"not_trade_feedback":True}
 ]
 return {"phase135_daily_brief_feedback_intake":{"total":len(feedbacks),"feedbacks":feedbacks,"empty_feedback_ready":True,"mock_used":False,"fixture_used":False}}
