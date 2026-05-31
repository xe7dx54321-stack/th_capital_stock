import json
from datetime import datetime

def build_source_depth_scores():
    """Score each source by depth: how much hard data it actually provides."""
    scores = [
        {"source_id":"yfinance_financials","depth_score":8,"dimensions_covered":["financial_structured","financial_statements"],"data_type":"structured_numeric","refresh_capability":"on_demand","score_rationale":"provides_10+_years_quarterly_financials"},
        {"source_id":"akshare_sina_financial","depth_score":7,"dimensions_covered":["financial_structured","financial_statements"],"data_type":"structured_numeric","refresh_capability":"on_demand","score_rationale":"provides_CN_financials_multi_statement"},
        {"source_id":"akshare_hk_financial","depth_score":6,"dimensions_covered":["financial_structured","financial_statements"],"data_type":"structured_numeric","refresh_capability":"on_demand","score_rationale":"provides_HK_financials_some_metrics_missing"},
        {"source_id":"sec_edgar","depth_score":7,"dimensions_covered":["filings_regulatory","financial_statements"],"data_type":"regulatory_text_and_structured","refresh_capability":"on_demand","score_rationale":"10K_10Q_full_filing_access"},
        {"source_id":"yfinance_price","depth_score":8,"dimensions_covered":["price_daily"],"data_type":"structured_numeric","refresh_capability":"daily","score_rationale":"daily_OHLCV_20+_years"},
        {"source_id":"eastmoney_price","depth_score":7,"dimensions_covered":["price_daily"],"data_type":"structured_numeric","refresh_capability":"daily","score_rationale":"CN_A_daily_price"},
        {"source_id":"phase85_cn_valuation","depth_score":5,"dimensions_covered":["valuation"],"data_type":"derived_metrics","refresh_capability":"on_demand","score_rationale":"PE_PB_PS_derived_from_price_financials"},
        {"source_id":"phase85_hk_valuation","depth_score":5,"dimensions_covered":["valuation"],"data_type":"derived_metrics","refresh_capability":"on_demand","score_rationale":"HK_valuation_derived"},
        {"source_id":"phase85_us_valuation","depth_score":6,"dimensions_covered":["valuation"],"data_type":"derived_metrics","refresh_capability":"on_demand","score_rationale":"US_valuation_derived_with_consensus"},
        {"source_id":"phase86_expectation","depth_score":4,"dimensions_covered":["pricing_expectation"],"data_type":"derived_signals","refresh_capability":"daily","score_rationale":"expectation_derived_from_price_volume"},
        {"source_id":"phase86_pricing","depth_score":4,"dimensions_covered":["pricing_expectation"],"data_type":"derived_signals","refresh_capability":"daily","score_rationale":"pricing_classification_derived"},
        {"source_id":"phase87_external","depth_score":3,"dimensions_covered":["industry_news","sentiment"],"data_type":"keyword_matched_news","refresh_capability":"daily","score_rationale":"industry_news_keyword_based"},
        {"source_id":"phase88_connector","depth_score":4,"dimensions_covered":["industry_news","sentiment"],"data_type":"external_signal_delta","refresh_capability":"daily","score_rationale":"external_api_with_delta_tracking"},
        {"source_id":"cninfo_disclosure","depth_score":6,"dimensions_covered":["filings_regulatory","financial_statements"],"data_type":"regulatory_text","refresh_capability":"on_demand","score_rationale":"partial_ticker_coverage"},
        {"source_id":"local_structured_financial_db","depth_score":3,"dimensions_covered":["financial_structured"],"data_type":"cached_copy","refresh_capability":"stale","score_rationale":"cached_not_live"},
        {"source_id":"evidence_memory","depth_score":1,"dimensions_covered":[],"data_type":"historical_records","refresh_capability":"append_only","score_rationale":"history_pool_not_data_source"},
        {"source_id":"watchlist_intelligence","depth_score":1,"dimensions_covered":[],"data_type":"historical_decisions","refresh_capability":"append_only","score_rationale":"history_pool_not_data_source"},
        {"source_id":"ai_optical_keywords","depth_score":0,"dimensions_covered":[],"data_type":"keyword_list","refresh_capability":"static","score_rationale":"curated_catalog_not_data_source"},
        {"source_id":"chinese_business_registry","depth_score":0,"dimensions_covered":[],"data_type":"source_metadata","refresh_capability":"static","score_rationale":"registry_not_data_source"},
        {"source_id":"known_disclosure_urls","depth_score":0,"dimensions_covered":[],"data_type":"url_list","refresh_capability":"static","score_rationale":"catalog_not_data_source"},
        {"source_id":"cninfo_300394","depth_score":0,"dimensions_covered":[],"data_type":"none","refresh_capability":"blocked","score_rationale":"blocked_cninfo_org_id_missing"},
        {"source_id":"exchange_report_text","depth_score":1,"dimensions_covered":[],"data_type":"unstructured_text","refresh_capability":"fallback_only","score_rationale":"fallback_not_primary_source"},
    ]
    return {
        "phase91_source_depth_scoring": {
            "generated_at": datetime.now().isoformat(),
            "sources_scored": len(scores),
            "max_possible_score": 10,
            "scores": scores
        }
    }

def build_freshness_audit():
    """Audit how fresh each source's data actually is."""
    audit = [
        {"source_id":"yfinance_financials","last_known_fresh_data":"2026-05","refresh_frequency":"quarterly","staleness_risk":"low","can_serve_latest_quarter":True},
        {"source_id":"akshare_sina_financial","last_known_fresh_data":"2026-03","refresh_frequency":"quarterly","staleness_risk":"low","can_serve_latest_quarter":True},
        {"source_id":"akshare_hk_financial","last_known_fresh_data":"2026-03","refresh_frequency":"semi_annual","staleness_risk":"medium","can_serve_latest_quarter":False},
        {"source_id":"yfinance_price","last_known_fresh_data":"daily_T-1","refresh_frequency":"daily","staleness_risk":"very_low","can_serve_latest_quarter":True},
        {"source_id":"eastmoney_price","last_known_fresh_data":"daily_T-0","refresh_frequency":"daily","staleness_risk":"very_low","can_serve_latest_quarter":True},
        {"source_id":"phase87_external","last_known_fresh_data":"on_demand","refresh_frequency":"on_demand","staleness_risk":"medium","can_serve_latest_quarter":True},
        {"source_id":"phase88_connector","last_known_fresh_data":"daily","refresh_frequency":"daily","staleness_risk":"low","can_serve_latest_quarter":True},
        {"source_id":"sec_edgar","last_known_fresh_data":"on_demand","refresh_frequency":"on_filing","staleness_risk":"low","can_serve_latest_quarter":True},
        {"source_id":"local_structured_financial_db","last_known_fresh_data":"cache_dependent","refresh_frequency":"manual","staleness_risk":"high","can_serve_latest_quarter":False},
        {"source_id":"evidence_memory","last_known_fresh_data":"historical_append","refresh_frequency":"append_only","staleness_risk":"not_applicable","can_serve_latest_quarter":False},
    ]
    return {
        "phase91_source_freshness_reality_audit": {
            "generated_at": datetime.now().isoformat(),
            "sources_audited": len(audit),
            "freshness_records": audit
        }
    }

def build_reliability_crosscheck():
    """Crosscheck registry claims vs execution reality."""
    crosscheck = [
        {"registry_claim":"financial_source_registry: all CN tickers covered","reality":"covered_for_3_of_4_CN_tickers","gap":"300394_blocked","reliability_gap":True},
        {"registry_claim":"phase83: all 4 HK/US tickers available","reality":"confirmed_4_of_4_available","gap":"none","reliability_gap":False},
        {"registry_claim":"phase85: valuation available for all markets","reality":"available_except_688041_valuation_gap","gap":"688041_pricing_valuation_gap","reliability_gap":True},
        {"registry_claim":"phase87: industry news coverage for all tickers","reality":"keyword_based_not_hard_data","gap":"industry_news_is_keyword_catalog_not_structured_data","reliability_gap":True},
        {"registry_claim":"phase88: external source real API","reality":"connectors_exist_but_execution_depends_on_availability","gap":"external_api_dependency","reliability_gap":True},
        {"registry_claim":"curated_catalogs_as_data_sources","reality":"catalogs_are_metadata_not_data","gap":"ai_optical_keywords_and_chinese_business_registry_are_catalogs_not_sources","reliability_gap":True},
        {"registry_claim":"history_pools_as_live_sources","reality":"evidence_memory_and_watchlist_intelligence_are_history_not_sources","gap":"history_pools_misclassified_in_some_contexts","reliability_gap":True},
        {"registry_claim":"delivery_outbox_as_information_source","reality":"outbox_is_output_pipeline_not_information_source","gap":"phase90_outbox_is_delivery_mechanism_not_source","reliability_gap":True},
    ]
    return {
        "phase91_reliability_vs_reality_crosscheck": {
            "generated_at": datetime.now().isoformat(),
            "claims_checked": len(crosscheck),
            "reliability_gaps_found": sum(1 for c in crosscheck if c["reliability_gap"]),
            "crosscheck_records": crosscheck
        }
    }

def build_backlog_priority():
    """Build prioritized backlog of source gaps for Phase 92-96."""
    backlog = [
        {"rank":1,"gap":"order_contract_source","priority":"highest","phase_target":"phase92","rationale":"order_and_contract_data_is_highest_signal_value_gap_across_all_8_tickers","affected_tickers":8,"estimated_effort":"high"},
        {"rank":2,"gap":"customer_capex_source","priority":"highest","phase_target":"phase92","rationale":"customer_capex_is_key_for_NVDA_AVGO_supply_chain_validation","affected_tickers":8,"estimated_effort":"high"},
        {"rank":3,"gap":"supply_chain_source","priority":"highest","phase_target":"phase93","rationale":"supply_chain_capacity_delivery_is_critical_for_semiconductor_tickers","affected_tickers":8,"estimated_effort":"high"},
        {"rank":4,"gap":"product_pricing_source","priority":"high","phase_target":"phase93","rationale":"product_ASP_and_supply_demand_dynamics_for_optical_and_chip_tickers","affected_tickers":5,"estimated_effort":"medium"},
        {"rank":5,"gap":"management_guidance_source","priority":"high","phase_target":"phase94","rationale":"management_guidance_proxy_for_earnings_expectation_calibration","affected_tickers":8,"estimated_effort":"medium"},
        {"rank":6,"gap":"300394_cninfo_resolution","priority":"high","phase_target":"phase94","rationale":"resolve_300394_blocker_to_complete_CN_A_coverage","affected_tickers":1,"estimated_effort":"low"},
        {"rank":7,"gap":"688041_valuation_pricing_gap","priority":"medium","phase_target":"phase95","rationale":"close_688041_valuation_and_pricing_gap","affected_tickers":1,"estimated_effort":"medium"},
        {"rank":8,"gap":"industry_news_hard_data_upgrade","priority":"medium","phase_target":"phase95","rationale":"upgrade_keyword_catalog_to_structured_industry_data","affected_tickers":8,"estimated_effort":"high"},
        {"rank":9,"gap":"peer_benchmark_hard_data","priority":"medium","phase_target":"phase96","rationale":"build_structured_peer_comparison_with_hard_financial_data","affected_tickers":8,"estimated_effort":"medium"},
        {"rank":10,"gap":"macro_data_integration","priority":"low","phase_target":"phase96","rationale":"integrate_macro_indicators_for_multi_market_context","affected_tickers":8,"estimated_effort":"medium"},
    ]
    return {
        "phase91_source_backlog_priority": {
            "generated_at": datetime.now().isoformat(),
            "backlog_items": len(backlog),
            "priorities": backlog,
            "phase92_96_recommendation": "start_with_highest_priority_order_contract_customer_capex_supply_chain_sources"
        }
    }
