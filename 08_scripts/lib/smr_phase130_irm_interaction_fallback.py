def build_irm_interaction_fallback():
 sources=[
  {"source_id":"irm_cninfo_interaction","url":"https://irm.cninfo.com.cn","type":"investor_relations","content_type":"investor_qa_and_interactions","access":"free_no_key","status":"available","data_quality":"official","note":"CNINFO IRM platform, investor Q&A with listed companies, may contain 300394 interactions","requires_stock_code_search":True},
  {"source_id":"szse_interaction_easy","url":"https://irm.szse.cn","type":"investor_relations","content_type":"investor_interactions","access":"free_no_key","status":"available","data_quality":"official","note":"SZSE E-interaction platform, official investor Q&A"},
 ]
 return {"phase130_irm_interaction_fallback":{"total":len(sources),"available":sum(1 for s in sources if s["status"]=="available"),"sources":sources,"coverage":"investor_relations_and_qa","complementary_to_financial_filings":True,"mock_used":False,"fixture_used":False}}
