import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase131_eastmoney_financial_adapter import build_eastmoney_financial_adapter
from smr_phase131_szse_disclosure_adapter import build_szse_disclosure_adapter
from smr_phase131_irm_interaction_adapter import build_irm_interaction_adapter
from smr_phase131_company_ir_adapter import build_company_ir_adapter
def build_known_url_integration():
 eastmoney=build_eastmoney_financial_adapter()["phase131_eastmoney_financial_adapter"]["adapter"]
 szse=build_szse_disclosure_adapter()["phase131_szse_disclosure_adapter"]["adapter"]
 irm=build_irm_interaction_adapter()["phase131_irm_interaction_adapter"]["adapter"]
 ir=build_company_ir_adapter()["phase131_company_ir_adapter"]["adapter"]
 urls=[{"source_id":eastmoney["source_id"],"url":eastmoney["url"],"purpose":"primary_financial_data","status":"integrated"},{"source_id":szse["source_id"],"url":szse["company_page_url"],"purpose":"official_disclosure_fallback","status":"integrated"},{"source_id":irm["source_id"],"url":irm["cninfo_irm_url"],"purpose":"investor_qa","status":"integrated"},{"source_id":ir["source_id"],"url":ir["ir_url"],"purpose":"company_ir","status":"integrated_pending_verification"}]
 return {"phase131_known_url_integration_loader":{"total":len(urls),"integrated":sum(1 for u in urls if u["status"]=="integrated"),"pending":sum(1 for u in urls if "pending" in u["status"]),"urls":urls,"mock_used":False,"fixture_used":False}}
