def build_szse_disclosure_fallback():
 sources=[
  {"source_id":"szse_company_page","url":"https://www.szse.cn/certificate/individual/index.html?code=300394","type":"official_exchange","content_type":"company_profile_and_announcements","access":"free_no_key","status":"available","data_quality":"official","note":"SZSE official company page, includes announcements and filings"},
  {"source_id":"szse_disclosure_search","url":"http://disc.static.szse.cn/download","type":"official_exchange","content_type":"periodic_reports","access":"free_no_key","status":"url_pattern_known","data_quality":"official","note":"SZSE disclosure download page for periodic reports"},
  {"source_id":"szse_announcement_list","url":"https://www.szse.cn/disclosure/listed/notice/index.html","type":"official_exchange","content_type":"announcements","access":"free_no_key","status":"available","data_quality":"official","note":"SZSE listed company announcement list, searchable by stock code"},
 ]
 return {"phase130_szse_disclosure_fallback":{"total":len(sources),"available":sum(1 for s in sources if s["status"]=="available"),"sources":sources,"coverage":"official_exchange_disclosure","cninfo_equivalent_for_filings":True,"mock_used":False,"fixture_used":False}}
