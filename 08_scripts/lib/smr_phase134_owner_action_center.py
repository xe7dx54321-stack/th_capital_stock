def build_owner_action_center():
 actions=[
  {"action_id":"OA-134-001","ticker":"ALL","market":"ALL","action":"review_personal_research_console","priority":"today","type":"research_review","status":"ready","trade_action":False},
  {"action_id":"OA-134-002","ticker":"688041.SH","market":"CN_A","action":"review_valuation_derived_metrics","priority":"this_week","type":"deep_dive","status":"ready","trade_action":False},
  {"action_id":"OA-134-003","ticker":"NVDA","market":"US","action":"review_seasonal_financial_trend","priority":"this_week","type":"deep_dive","status":"ready","trade_action":False},
  {"action_id":"OA-134-004","ticker":"300394.SZ","market":"CN_A","action":"continue_cninfo_identity_resolution","priority":"ongoing","type":"source_fix","status":"in_progress","trade_action":False},
  {"action_id":"OA-134-005","ticker":"09988.HK","market":"HK","action":"monitor_cloud_revenue_acceleration","priority":"next_quarter","type":"routine_monitoring","status":"ready","trade_action":False}
 ]
 return {"phase134_owner_action_center":{"owner_actions_created":len(actions),"actions":actions,"trade_actions":0,"not_trade_signal":True,"mock_used":False,"fixture_used":False}}
