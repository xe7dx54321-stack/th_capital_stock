def build_expansion_board():
 items=[
  {"section":"registry","item":"total_source_candidates","status":"defined","detail":"11 sources (5 official + 6 third_party)"},
  {"section":"registry","item":"official_filings","status":"defined","detail":"6 filing types (HKEX + SEC + CNINFO)"},
  {"section":"registry","item":"market_quotes","status":"defined","detail":"3 quote sources"},
  {"section":"registry","item":"news_events","status":"defined","detail":"5 news sources"},
  {"section":"registry","item":"transcripts","status":"defined","detail":"4 transcript sources"},
  {"section":"adapter","item":"hk_adapter","status":"defined","detail":"09988/00700: 2->6 sources"},
  {"section":"adapter","item":"us_adapter","status":"defined","detail":"NVDA/AVGO: 1->8 sources"},
  {"section":"probe","item":"network_probe","status":"pending","detail":"12 sources need network probe"},
  {"section":"risk","item":"nvda_single_source","status":"reduced_planned","detail":"NVDA: critical->moderate"},
  {"section":"risk","item":"avgo_single_source","status":"reduced_planned","detail":"AVGO: critical->moderate"},
  {"section":"gaps","item":"300394","status":"unchanged","detail":"CNINFO blocker retained"},
  {"section":"gaps","item":"688041","status":"unchanged","detail":"Valuation gap retained"},
 ]
 return {"phase121_expansion_board":{"total":len(items),"sections":["registry","adapter","probe","risk","gaps"],"items":items,"not_trade_board":True,"research_only":True,"mock_used":False,"fixture_used":False}}
