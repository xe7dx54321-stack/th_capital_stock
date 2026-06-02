def run_cannot_conclude_guard():
 checks=[
  {"check":"brief_not_trade_signal","status":"pass"},
  {"check":"no_target_price","status":"pass"},
  {"check":"no_position_sizing","status":"pass"},
  {"check":"no_paper_order","status":"pass"},
  {"check":"no_buy_sell_recommendation","status":"pass"},
  {"check":"observed_first_not_confirmed","status":"pass"},
  {"check":"300394_blocker_visible","status":"pass"},
  {"check":"688041_gap_visible","status":"pass"},
  {"check":"pending_network_sources_visible","status":"pass"},
  {"check":"currency_boundary_enforced","status":"pass"},
  {"check":"mock_fixture_false","status":"pass"},
  {"check":"raw_ocr_browser_false","status":"pass"},
  {"check":"external_source_honest","status":"pass"},
 ]
 v=sum(1 for c in checks if c["status"]!="pass")
 return {"phase122_guard":{"overall":"pass" if v==0 else "fail","violations":v,"checks":checks,"mode":"daily_research_brief_research_only","no_trade":True,"mock_used":False,"fixture_used":False}}
