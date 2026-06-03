def build_owner_action_feedback_intake():
 feedbacks=[
  {"feedback_id":"FB-OA-001","created_at":"2026-06-03T00:00:00Z","feedback_type":"request_deep_dive","source_console_section":"owner_action_center","target_ticker":"688041.SH","target_entity_id":"OA-134-002","owner_comment":"Deep dive 688041 valuation gap close","impact_scope":"deep_dive_task","validation_status":"valid","research_only":True,"not_trade_feedback":True}
 ]
 return {"phase135_owner_action_feedback_intake":{"total":len(feedbacks),"feedbacks":feedbacks,"empty_feedback_ready":True,"mock_used":False,"fixture_used":False}}
