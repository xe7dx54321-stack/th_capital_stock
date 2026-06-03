def build_third_party_equivalent_registry():
 equivalents=[
  {"official_source":"sec_edgar","equivalent_id":"yfinance_financials","equivalent_status":"available","data_match":"financial_statements","quality":"high","limitation":"may_not_have_all_exhibits"},
  {"official_source":"sec_10k","equivalent_id":"yfinance_annual","equivalent_status":"available","data_match":"annual_financials","quality":"high","limitation":"XBRL-tagged data only"},
  {"official_source":"sec_10q","equivalent_id":"yfinance_quarterly","equivalent_status":"available","data_match":"quarterly_financials","quality":"high","limitation":"XBRL-tagged data only"},
  {"official_source":"sec_8k","equivalent_id":"finviz_news","equivalent_status":"available","data_match":"material_events","quality":"medium","limitation":"news coverage, not raw filings"},
  {"official_source":"hkex_news","equivalent_id":"akshare_hk_news","equivalent_status":"available","data_match":"announcements","quality":"high","limitation":"structured format differs from HKEX RSS"},
  {"official_source":"hkex_filing","equivalent_id":"akshare_hk_financials","equivalent_status":"available","data_match":"financial_filings","quality":"high","limitation":"metric mapping needed for some fields"},
  {"official_source":"transcript_guidance_manual","equivalent_id":"manual_required","equivalent_status":"manual_required","data_match":"partial","quality":"varies","limitation":"full transcripts require paid service or manual work"},
 ]
 return {"phase129_third_party_equivalent_registry":{"total":len(equivalents),"available":sum(1 for e in equivalents if e["equivalent_status"]=="available"),"manual_required":sum(1 for e in equivalents if e["equivalent_status"]=="manual_required"),"equivalents":equivalents,"mock_used":False,"fixture_used":False}}
