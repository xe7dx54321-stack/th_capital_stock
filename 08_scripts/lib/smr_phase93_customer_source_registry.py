import json,os
from datetime import datetime
from pathlib import Path

def build_customer_source_registry():
    sources = [
        {"source_id":"customer_10k_10q","source_type":"regulatory_filing","market":"US","provides":"customer_capex_data","target_customers":["Microsoft","Amazon","Google","Meta"],"requires_network":True},
        {"source_id":"customer_earnings_call","source_type":"earnings_transcript","market":"US,HK","provides":"customer_capex_guidance","target_customers":["Microsoft","Amazon","Google","Meta","Oracle","Alibaba","Tencent"],"requires_network":True,"note":"transcript_availability_varies"},
        {"source_id":"sec_companyfacts","source_type":"structured_filing_data","market":"US","provides":"customer_financial_metrics","target_customers":["Microsoft","Amazon","Google","Meta"],"requires_network":True},
        {"source_id":"cninfo_customer_procurement","source_type":"disclosure_platform","market":"CN_A","provides":"customer_procurement_announcements","target_customers":["ChinaTelecom","ChinaMobile","ChinaUnicom"],"requires_network":True,"blocked_tickers":["300394.SZ"]},
        {"source_id":"operator_procurement_platform","source_type":"procurement_platform","market":"CN_A","provides":"operator_procurement_notices","target_customers":["ChinaTelecom","ChinaMobile","ChinaUnicom"],"requires_network":True},
        {"source_id":"government_procurement","source_type":"procurement_platform","market":"CN_A","provides":"government_procurement_notices","target_customers":["Government","Education"],"requires_network":True},
        {"source_id":"customer_ir_news","source_type":"company_website","market":"US,HK,CN_A","provides":"customer_investment_news","target_customers":["All"],"requires_network":True},
        {"source_id":"yfinance_customer_financials","source_type":"financial_data_api","market":"US,HK","provides":"customer_financial_metrics","target_customers":["Microsoft","Amazon","Google","Meta","Alibaba","Tencent"],"requires_network":True},
        {"source_id":"phase87_external_news","source_type":"existing_connector","market":"CN_A,HK,US","provides":"industry_customer_news","target_customers":["All"],"requires_network":True},
        {"source_id":"existing_text_pool","source_type":"local_text_pool","market":"CN_A","provides":"previously_collected_text","target_customers":["CN_customers"],"requires_network":False},
        {"source_id":"manual_customer_research","source_type":"manual_required","market":"CN_A,HK,US","provides":"manual_customer_analysis","target_customers":["All"],"requires_network":False,"note":"manual_research_required_no_automation"},
    ]
    return {"phase93_customer_source_registry":{
        "generated_at":datetime.now().isoformat(),
        "customer_sources_registered":len(sources),
        "sources":sources,
        "mock_used":False,"fixture_used":False
    }}
