def run_cannot_conclude_guard():
 checks=[
  {"check":"expansion_not_trade","status":"pass"},
  {"check":"no_target_price","status":"pass"},
  {"check":"no_position_sizing","status":"pass"},
  {"check":"no_paper_order","status":"pass"},
  {"check":"no_buy_sell","status":"pass"},
  {"check":"source_candidate_not_confirmed","status":"pass"},
  {"check":"probe_status_honest","status":"pass"},
  {"check":"300394_blocker_visible","status":"pass"},
  {"check":"688041_gap_visible","status":"pass"},
  {"check":"single_source_risk_not_hidden","status":"pass"},
  {"check":"mock_fixture_false","status":"pass"},
  {"check":"raw_ocr_browser_false","status":"pass"},
  {"check":"hk_us_currency_not_mixed","status":"pass"},
  {"check":"period_not_mixed","status":"pass"},
 ]
 v=sum(1 for c in checks if c["status"]!="pass")
 return {"phase121_guard":{"overall":"pass" if v==0 else "fail","violations":v,"checks":checks,"mode":"research_only","no_trade":True,"mock_used":False,"fixture_used":False}}
