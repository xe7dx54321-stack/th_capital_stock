import json,os
from datetime import datetime

def build_supply_chain_source_registry():
    sources = [
        {"source_id":"supplier_disclosure","source_type":"company_disclosure","market":"CN_A,HK,US","provides":"supplier_capacity_expansion_data","requires_network":True},
        {"source_id":"peer_disclosure","source_type":"company_disclosure","market":"CN_A,HK,US","provides":"peer_delivery_capacity_commentary","requires_network":True},
        {"source_id":"industry_news_connector","source_type":"news_aggregation","market":"CN_A,HK,US","provides":"industry_supply_demand_news","requires_network":True},
        {"source_id":"exchange_announcement","source_type":"regulatory","market":"CN_A,HK","provides":"supply_chain_related_announcements","requires_network":True,"blocked_tickers":["300394.SZ"]},
        {"source_id":"company_ir_supply_commentary","source_type":"investor_relations","market":"CN_A,HK,US","provides":"management_supply_chain_commentary","requires_network":True},
        {"source_id":"existing_pdf_text_pool","source_type":"local_text_pool","market":"CN_A","provides":"previously_extracted_text","requires_network":False},
        {"source_id":"phase92_order_text","source_type":"existing_evidence","market":"CN_A,HK,US","provides":"order_text_with_supplier_references","requires_network":False,"note":"linkage_source"},
        {"source_id":"sec_supplier_filings","source_type":"regulatory_filing","market":"US","provides":"supplier_and_customer_relationships","requires_network":True},
        {"source_id":"yfinance_supplier_news","source_type":"financial_data_api","market":"US,HK","provides":"supplier_related_news","requires_network":True},
        {"source_id":"known_url_catalog","source_type":"url_catalog","market":"CN_A","provides":"known_supplier_urls","requires_network":True},
        {"source_id":"manual_supply_research","source_type":"manual_required","market":"CN_A,HK,US","provides":"manual_supply_chain_analysis","requires_network":False,"note":"manual_research_required"},
    ]
    return {"phase93_supply_chain_source_registry":{
        "generated_at":datetime.now().isoformat(),
        "supply_chain_sources_registered":len(sources),
        "sources":sources,
        "mock_used":False,"fixture_used":False
    }}
