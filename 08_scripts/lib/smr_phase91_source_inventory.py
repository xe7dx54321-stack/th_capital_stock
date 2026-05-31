import json, os, sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def _load_json(rel_path):
    p = PROJECT_ROOT / rel_path
    if p.exists():
        with open(p, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {}

def build_source_inventory():
    """Build comprehensive source inventory from all known registries and adapters."""
    sources = []
    
    # 1. Financial structured APIs
    sources.append({"source_id":"akshare_sina_financial","source_type":"third_party_api","registry":"financial_source_registry.json","provides":"CN_A_financial_statements","network_required":True,"markets":["CN_A"],"reality_class":"needs_classification"})
    sources.append({"source_id":"akshare_hk_financial","source_type":"third_party_api","registry":"phase83_hk_us_financial_adapters.json","provides":"HK_financial_statements","network_required":True,"markets":["HK"],"reality_class":"needs_classification"})
    sources.append({"source_id":"yfinance_financials","source_type":"third_party_api","registry":"phase83_hk_us_financial_adapters.json","provides":"HK_US_financial_statements","network_required":True,"markets":["HK","US"],"reality_class":"needs_classification"})
    sources.append({"source_id":"local_structured_financial_db","source_type":"local_database","registry":"financial_source_registry.json","provides":"cached_financial_data","network_required":False,"markets":["CN_A"],"reality_class":"needs_classification"})
    
    # 2. Price data
    sources.append({"source_id":"eastmoney_price","source_type":"third_party_api","registry":"inferred","provides":"CN_A_daily_price","network_required":True,"markets":["CN_A"],"reality_class":"needs_classification"})
    sources.append({"source_id":"yfinance_price","source_type":"third_party_api","registry":"phase83_hk_us_financial_adapters.json","provides":"HK_US_daily_price","network_required":True,"markets":["HK","US"],"reality_class":"needs_classification"})
    
    # 3. Regulatory disclosures
    sources.append({"source_id":"cninfo_disclosure","source_type":"regulatory_disclosure","registry":"chinese_business_source_registry.json","provides":"CN_A_filings","network_required":True,"markets":["CN_A"],"reality_class":"needs_classification","known_issue":"blocked_for_300394"})
    sources.append({"source_id":"sec_edgar","source_type":"regulatory_disclosure","registry":"phase83_hk_us_financial_adapters.json","provides":"US_filings","network_required":True,"markets":["US"],"reality_class":"needs_classification"})
    sources.append({"source_id":"hkex_disclosure","source_type":"regulatory_disclosure","registry":"phase83_hk_us_financial_adapters.json","provides":"HK_filings","network_required":True,"markets":["HK"],"reality_class":"needs_classification"})
    
    # 4. Valuation adapters
    sources.append({"source_id":"phase85_cn_valuation","source_type":"derived_adapter","registry":"phase85_valuation_integration.json","provides":"CN_A_valuation","network_required":False,"markets":["CN_A"],"reality_class":"needs_classification"})
    sources.append({"source_id":"phase85_hk_valuation","source_type":"derived_adapter","registry":"phase85_valuation_integration.json","provides":"HK_valuation","network_required":False,"markets":["HK"],"reality_class":"needs_classification"})
    sources.append({"source_id":"phase85_us_valuation","source_type":"derived_adapter","registry":"phase85_valuation_integration.json","provides":"US_valuation","network_required":False,"markets":["US"],"reality_class":"needs_classification"})
    
    # 5. Expectation/Pricing
    sources.append({"source_id":"phase86_expectation","source_type":"derived_adapter","registry":"phase86_expectation_market_pricing.json","provides":"expectation_signals","network_required":False,"markets":["CN_A","HK","US"],"reality_class":"needs_classification"})
    sources.append({"source_id":"phase86_pricing","source_type":"derived_adapter","registry":"phase86_expectation_market_pricing.json","provides":"pricing_signals","network_required":False,"markets":["CN_A","HK","US"],"reality_class":"needs_classification"})
    
    # 6. External/News
    sources.append({"source_id":"phase87_external","source_type":"keyword_catalog_with_api","registry":"phase87_external_source_integration.json","provides":"industry_news","network_required":True,"markets":["CN_A","HK","US"],"reality_class":"needs_classification"})
    sources.append({"source_id":"phase88_connector","source_type":"connector_registry","registry":"phase88_external_daily_signal_delta.json","provides":"external_signals","network_required":True,"markets":["CN_A","HK","US"],"reality_class":"needs_classification"})
    
    # 7. Curated keyword catalogs (NOT hard data sources)
    sources.append({"source_id":"ai_optical_keywords","source_type":"curated_catalog","registry":"ai_optical_business_keywords.json","provides":"industry_keywords_only","network_required":False,"markets":["CN_A"],"reality_class":"needs_classification","note":"curated_catalog_not_hard_data"})
    sources.append({"source_id":"chinese_business_registry","source_type":"curated_catalog","registry":"chinese_business_source_registry.json","provides":"source_metadata_only","network_required":False,"markets":["CN_A"],"reality_class":"needs_classification","note":"registry_not_data_source"})
    sources.append({"source_id":"known_disclosure_urls","source_type":"curated_catalog","registry":"known_disclosure_url_catalog.json","provides":"url_endpoints_only","network_required":False,"markets":["CN_A"],"reality_class":"needs_classification","note":"catalog_not_data_source"})
    sources.append({"source_id":"alternative_disclosure","source_type":"curated_catalog","registry":"alternative_disclosure_sources.json","provides":"alternative_endpoints_only","network_required":False,"markets":["CN_A"],"reality_class":"needs_classification","note":"catalog_not_data_source"})
    
    # 8. History pools (NOT live sources)
    sources.append({"source_id":"evidence_memory","source_type":"history_pool","registry":"evidence_memory_schema.json","provides":"historical_evidence","network_required":False,"markets":["CN_A","HK","US"],"reality_class":"needs_classification","note":"history_pool_not_live_source"})
    sources.append({"source_id":"watchlist_intelligence","source_type":"history_pool","registry":"phase89_unified_daily_intelligence.json","provides":"historical_decisions","network_required":False,"markets":["CN_A","HK","US"],"reality_class":"needs_classification","note":"history_pool_not_live_source"})
    sources.append({"source_id":"phase84_run_history","source_type":"history_pool","registry":"phase84_scheduled_daily_monitoring.json","provides":"run_history","network_required":False,"markets":["CN_A","HK","US"],"reality_class":"needs_classification","note":"history_pool_not_live_source"})
    sources.append({"source_id":"phase90_delivery_history","source_type":"history_pool","registry":"phase90_scheduled_automation_delivery.json","provides":"delivery_history","network_required":False,"markets":["CN_A","HK","US"],"reality_class":"needs_classification","note":"history_pool_not_live_source"})
    
    # 9. Blocked
    sources.append({"source_id":"cninfo_300394","source_type":"regulatory_disclosure","registry":"phase76_300394_known_url_candidates.json","provides":"300394_filings","network_required":True,"markets":["CN_A"],"reality_class":"needs_classification","blocker":"cninfo_org_id_missing","known_issue":"blocked"})
    
    # 10. Fallback/Manual
    sources.append({"source_id":"exchange_report_text","source_type":"fallback_text","registry":"phase83_hk_us_financial_adapters.json","provides":"HK_report_text","network_required":True,"markets":["HK"],"reality_class":"needs_classification","note":"fallback_only_not_primary"})
    sources.append({"source_id":"sec_10k_10q_text","source_type":"fallback_text","registry":"phase83_hk_us_financial_adapters.json","provides":"US_filing_text","network_required":True,"markets":["US"],"reality_class":"needs_classification","note":"fallback_only_not_primary"})
    sources.append({"source_id":"company_ir_pages","source_type":"manual_required","registry":"company_ir_page_candidates.json","provides":"IR_links","network_required":True,"markets":["CN_A","HK"],"reality_class":"needs_classification","note":"manual_required_no_automation"})
    
    # 11. Derived monitoring boards (outputs, not sources)
    sources.append({"source_id":"phase82_monitoring_board","source_type":"derived_output","registry":"phase82_multi_ticker_financial_coverage.json","provides":"monitoring_board","network_required":False,"markets":["CN_A","HK","US"],"reality_class":"needs_classification","note":"output_not_source"})
    sources.append({"source_id":"phase84_portfolio_board","source_type":"derived_output","registry":"phase84_scheduled_daily_monitoring.json","provides":"portfolio_board","network_required":False,"markets":["CN_A","HK","US"],"reality_class":"needs_classification","note":"output_not_source"})
    sources.append({"source_id":"phase89_unified_board","source_type":"derived_output","registry":"phase89_unified_daily_intelligence.json","provides":"unified_board","network_required":False,"markets":["CN_A","HK","US"],"reality_class":"needs_classification","note":"output_not_source"})
    sources.append({"source_id":"phase90_outbox","source_type":"delivery_outbox","registry":"phase90_scheduled_automation_delivery.json","provides":"daily_report_output","network_required":False,"markets":["CN_A","HK","US"],"reality_class":"needs_classification","note":"delivery_outbox_not_source"})
    
    return {"phase91_existing_source_inventory": {
        "generated_at": datetime.now().isoformat(),
        "sources_inventoried": len(sources),
        "sources": sources
    }}
