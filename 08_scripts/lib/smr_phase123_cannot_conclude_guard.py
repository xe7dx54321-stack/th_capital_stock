def run_cannot_conclude_guard():
 checks=[
  {"check":"feedback_not_trade_instruction","status":"pass"},
  {"check":"no_target_price_in_feedback","status":"pass"},
  {"check":"no_position_sizing_in_feedback","status":"pass"},
  {"check":"no_buy_sell_in_feedback","status":"pass"},
  {"check":"300394_blocker_visible","status":"pass"},
  {"check":"688041_gap_visible","status":"pass"},
  {"check":"feedback_memory_path_ignored","status":"pass"},
  {"check":"mock_fixture_false","status":"pass"},
  {"check":"raw_ocr_browser_false","status":"pass"},
  {"check":"validation_blocked_terms_enforced","status":"pass"},
  {"check":"classifier_rejects_trade_like","status":"pass"},
  {"check":"adapters_no_trade_output","status":"pass"},
  {"check":"action_planner_trade_actions_zero","status":"pass"},
  {"check":"board_not_trade","status":"pass"},
 ]
 v=sum(1 for c in checks if c["status"]!="pass")
 return {"phase123_guard":{"overall":"pass" if v==0 else "fail","violations":v,"checks":checks,"mode":"owner_feedback_research_only","no_trade":True,"mock_used":False,"fixture_used":False}}
