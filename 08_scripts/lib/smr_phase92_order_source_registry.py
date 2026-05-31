import json,os
from datetime import datetime

def build_order_source_registry():
    sources = [
        {"source_id":"cninfo_keyword_search","source_type":"disclosure_platform","market":"CN_A","search_method":"keyword_match","endpoint_type":"api","requires_network":True,"known_blocked_for":["300394.SZ"],"blocked_reason":"cninfo_org_id_missing"},
        {"source_id":"exchange_disclosure_text_pool","source_type":"existing_text_pool","market":"CN_A","search_method":"text_scan","endpoint_type":"local","requires_network":False,"known_blocked_for":[]},
        {"source_id":"known_disclosure_url_catalog","source_type":"url_catalog","market":"CN_A","search_method":"url_fetch","endpoint_type":"http","requires_network":True,"known_blocked_for":["300394.SZ"]},
        {"source_id":"china_tender_platform","source_type":"government_procurement","market":"CN_A","search_method":"keyword_search","endpoint_type":"http","requires_network":True,"known_blocked_for":[],"note":"may_require_login_or_anti_crawl"},
        {"source_id":"china_gov_procurement","source_type":"government_procurement","market":"CN_A","search_method":"keyword_search","endpoint_type":"http","requires_network":True,"known_blocked_for":[],"note":"may_have_access_restrictions"},
        {"source_id":"operator_procurement_platform","source_type":"operator_procurement","market":"CN_A","search_method":"keyword_search","endpoint_type":"http","requires_network":True,"known_blocked_for":[]},
        {"source_id":"company_official_news","source_type":"company_website","market":"CN_A,HK,US","search_method":"page_scan","endpoint_type":"http","requires_network":True,"known_blocked_for":[]},
        {"source_id":"company_ir_page","source_type":"investor_relations","market":"CN_A,HK,US","search_method":"page_scan","endpoint_type":"http","requires_network":True,"known_blocked_for":[]},
        {"source_id":"sec_edgar_order_keyword","source_type":"regulatory_filing","market":"US","search_method":"keyword_search","endpoint_type":"api","requires_network":True,"known_blocked_for":[]},
        {"source_id":"yfinance_news","source_type":"financial_data_api","market":"HK,US","search_method":"news_search","endpoint_type":"api","requires_network":True,"known_blocked_for":[]},
        {"source_id":"phase87_external_connector","source_type":"existing_connector","market":"CN_A,HK,US","search_method":"connector_probe","endpoint_type":"api","requires_network":True,"known_blocked_for":[]},
        {"source_id":"phase88_daily_external","source_type":"existing_connector","market":"CN_A,HK,US","search_method":"delta_check","endpoint_type":"api","requires_network":True,"known_blocked_for":[]},
        {"source_id":"manual_fallback","source_type":"manual_required","market":"CN_A,HK,US","search_method":"manual","endpoint_type":"manual","requires_network":False,"known_blocked_for":[],"note":"manual_review_required"},
    ]
    return {"phase92_order_source_registry":{
        "generated_at":datetime.now().isoformat(),
        "order_sources_registered":len(sources),
        "sources":sources
    }}
