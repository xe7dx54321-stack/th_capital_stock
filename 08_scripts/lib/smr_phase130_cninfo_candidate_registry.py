def build_cninfo_candidate_registry():
 candidates=[
  {"candidate_id":"tianfu_communication_search","search_method":"cninfo_company_name_search","query":"天孚通信","expected_org_id":None,"status":"requires_manual_or_api_search","note":"CNINFO company name search may return org_id"},
  {"candidate_id":"stock_code_search","search_method":"cninfo_stock_code_search","query":"300394","expected_org_id":None,"status":"requires_manual_or_api_search","note":"CNINFO stock code search"},
  {"candidate_id":"szse_listed_company_lookup","search_method":"szse_public_company_list","query":"300394","expected_url":"https://www.szse.cn/certificate/individual/index.html?code=300394","status":"verifiable","note":"SZSE official company page"},
  {"candidate_id":"eastmoney_300394","search_method":"eastmoney_company_page","query":"300394","expected_url":"https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?type=web&code=300394","status":"verifiable","note":"Eastmoney financial data page, often mirrors CNINFO data"},
  {"candidate_id":"cninfo_org_id_manual_search","search_method":"manual_browser_search","query":"cninfo.com.cn 天孚通信 orgId","status":"manual_required","note":"Manually search CNINFO for org_id by visiting disclosure pages"}
 ]
 return {"phase130_cninfo_candidate_registry":{"total":len(candidates),"verifiable":sum(1 for c in candidates if c["status"]=="verifiable"),"manual_required":sum(1 for c in candidates if c["status"]=="manual_required"),"requires_api":sum(1 for c in candidates if c["status"]=="requires_manual_or_api_search"),"candidates":candidates,"no_confirmed_org_id":True,"mock_used":False,"fixture_used":False}}
