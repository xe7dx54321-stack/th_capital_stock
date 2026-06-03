def build_company_ir_loader():
 sources=[
  {"source_id":"tianfu_ir_website","url":"https://www.tfc-sz.com","type":"company_ir","content_type":"investor_relations_and_announcements","access":"free_no_key","status":"url_assumed","data_quality":"company_official","note":"Company official website, likely has IR section with financial reports"},
  {"source_id":"eastmoney_300394_profile","url":"https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?type=web&code=300394","type":"financial_data_aggregator","content_type":"financial_data_and_announcements","access":"free_no_key","status":"available","data_quality":"aggregated_official","note":"Eastmoney aggregates CNINFO/SZSE data, may serve as indirect CNINFO access"},
 ]
 return {"phase130_company_ir_loader":{"total":len(sources),"available":sum(1 for s in sources if s["status"]=="available"),"sources":sources,"coverage":"company_ir_and_data_aggregator","mock_used":False,"fixture_used":False}}
