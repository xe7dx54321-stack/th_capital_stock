import json,os
from datetime import datetime
def build_pricing_registry():
    sources=[
        {"source_id":"tender_procurement_price","type":"procurement","provides":"unit_price_from_tender","market":"CN_A","network":True},
        {"source_id":"annual_report_pricing","type":"disclosure","provides":"ASP_margin_commentary","market":"CN_A,HK,US","network":True},
        {"source_id":"industry_news_pricing","type":"news","provides":"price_trend_industry","market":"CN_A,HK,US","network":True},
        {"source_id":"supply_chain_upstream_price","type":"supply_chain","provides":"upstream_component_price","market":"CN_A,HK,US","network":True},
        {"source_id":"cloud_provider_list_price","type":"public_pricing","provides":"cloud_AI_service_pricing","market":"HK,US","network":True},
        {"source_id":"ir_interaction_pricing","type":"ir","provides":"management_pricing_commentary","market":"CN_A","network":True,"blocked_tickers":["300394.SZ"]},
        {"source_id":"sec_filing_pricing","type":"regulatory","provides":"pricing_risk_factor","market":"US","network":True},
        {"source_id":"existing_pdf_pool","type":"local","provides":"previously_extracted_pricing_text","market":"CN_A","network":False},
        {"source_id":"phase92_order_evidence","type":"existing","provides":"order_text_with_possible_pricing","market":"CN_A,HK,US","network":False,"note":"linkage_source"},
        {"source_id":"yfinance_product_news","type":"api","provides":"product_related_news","market":"HK,US","network":True},
        {"source_id":"manual_pricing_research","type":"manual","provides":"manual_price_collection","market":"CN_A,HK,US","network":False,"note":"manual_required"},
    ]
    return {"phase94_pricing_registry":{"generated_at":datetime.now().isoformat(),"pricing_sources":len(sources),"sources":sources,"mock_used":False,"fixture_used":False}}
