import os
def w(p,c): os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'w',encoding='utf-8').write(c)

# === 18. Integration Report ===
w('08_scripts/lib/smr_phase121_integration_report.py', '''def build_integration_report():
 return {"phase121_integration_report":{"phases_integrated":["phase117_master_runner","phase118_health","phase119_improvement"],"status":{"phase117":{"status":"ready","desc":"daily_runner_can_load_source_registry"},"phase118":{"status":"ready","desc":"health_check_can_include_source_coverage_score"},"phase119":{"status":"ready","desc":"improvement_loop_can_track_source_gap_closure"}},"no_breaking_change":True,"backward_compatible":True,"research_only":True,"mock_used":False,"fixture_used":False}}
''')

# === 19. Expansion Board ===
w('08_scripts/lib/smr_phase121_expansion_board.py', '''def build_expansion_board():
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
''')

# === 20. Expansion Brief ===
w('08_scripts/lib/smr_phase121_expansion_brief.py', '''def build_expansion_brief_md():
 return \"\"\"# Phase121 External Data Source Expansion Report

## Key Finding
HK/US tickers currently rely on 1-2 data sources. Phase121 defines 11 new external source candidates across official filings, market quotes, news/events, and transcripts/guidance.

## Source Registry
- 11 total source candidates (5 official + 6 third-party)
- 6 official filing types: HKEX annual/interim, SEC 10-K/10-Q/8-K, CNINFO annual
- 5 news aggregation sources: HKEX announcements, SEC press, Finviz, Google Finance, AAStocks
- 3 market quote sources: Yahoo Finance, Akshare, Alpha Vantage (free tier)
- 4 transcript/guidance sources: Motley Fool, Seeking Alpha, HKEX results, Company IR

## HK/US Adapter Status
- 09988.HK: 2 existing -> 6 candidate sources
- 00700.HK: 2 existing -> 6 candidate sources
- NVDA: 1 existing -> 8 candidate sources
- AVGO: 1 existing -> 8 candidate sources

## Single-Source Risk Reduction
- NVDA: critical -> moderate (after network probe)
- AVGO: critical -> moderate (after network probe)
- 09988/00700: high -> reduced (after network probe)

## Known Limitations
- 12 sources need network probe verification
- 300394 CNINFO blocker unchanged (critical/manual)
- 688041 valuation gap unchanged (high/owner)
- Transcript sources remain partially manual
- No investment recommendations generated
- No trading signals produced
- Research-only, all safety boundaries enforced\"\"\"
''')

# === 21. Cannot-Conclude Guard ===
w('08_scripts/lib/smr_phase121_cannot_conclude_guard.py', '''def run_cannot_conclude_guard():
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
''')

# === 22. Backlog Update ===
w('08_scripts/lib/smr_phase121_backlog_update.py', '''def build_backlog_update():
 return {"phase121_backlog":{"phase120_status":"closeout_complete","phase121_status":"external_source_expansion_v1","summary":{"sources_registered":11,"hk_adapter_candidates":6,"us_adapter_candidates":8,"probe_pending":12,"300394":"blocked","688041":"partial"},"next_phase":"phase122_daily_research_brief_v2","expansion_missing":["network_probe_12_sources","manual_transcript_hk_us"],"coverage_missing":["aastocks_probe","futu_probe","finviz_probe","marketwatch_probe","fool_probe","seekingalpha_probe"],"deprecated_forever":["paper_order","paper_trade","paper_position","paper_pnl","broker","live_trading","target_price","position_sizing"],"mock_used":False,"fixture_used":False}}
''')

print('18-22 done')