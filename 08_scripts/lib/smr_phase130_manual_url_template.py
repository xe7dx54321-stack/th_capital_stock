def build_manual_url_template():
 templates=[
  {"action":"search_cninfo_org_id","url_template":"https://www.cninfo.com.cn/new/disclosure/stock?stockCode=300394&orgId={orgId}","description":"Replace {orgId} with CNINFO org ID. Visit CNINFO, search 300394, find orgId in URL of any disclosure page.","estimated_time":"5-10 minutes","owner_action":"manual_browser_search"},
  {"action":"verify_szse_company_page","url":"https://www.szse.cn/certificate/individual/index.html?code=300394","description":"Visit SZSE official company page for 300394. Check if announcements and filings are downloadable.","estimated_time":"5 minutes","owner_action":"manual_browser_visit"},
  {"action":"search_eastmoney_financials","url":"https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?type=web&code=300394","description":"Visit Eastmoney 300394 page. Check financial data availability and announcement list.","estimated_time":"5 minutes","owner_action":"manual_browser_visit"},
  {"action":"check_company_ir","url":"https://www.tfc-sz.com","description":"Visit Tianfu Communication official website. Navigate to Investor Relations section. Check for financial reports and announcements.","estimated_time":"5-10 minutes","owner_action":"manual_browser_visit"},
  {"action":"irm_cninfo_interaction_search","url":"https://irm.cninfo.com.cn","description":"Visit CNINFO IRM platform. Search 300394. Review investor Q&A for business insights.","estimated_time":"10-15 minutes","owner_action":"manual_browser_search"},
  {"action":"record_findings","url":"N/A","description":"After verification, note which URLs work, which provide usable financial data, and whether a CNINFO org_id was found. Update config if org_id discovered.","estimated_time":"5 minutes","owner_action":"documentation"},
 ]
 return {"phase130_manual_url_template":{"total":len(templates),"all_require_owner_action":True,"templates":templates,"no_automation_possible":True,"mock_used":False,"fixture_used":False}}
