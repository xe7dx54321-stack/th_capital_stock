def build_stage_checklist():
    stages = {
        "candidate": {"checks": ["ticker_format_valid", "market_known", "not_duplicate"], "next_stage": "identity_verified"},
        "identity_verified": {"checks": ["ticker_identity_normalized", "name_confirmed", "market_confirmed"], "next_stage": "source_available"},
        "source_available": {"checks": ["primary_source_identified", "financial_data_accessible", "currency_known"], "next_stage": "financial_loaded"},
        "financial_loaded": {"checks": ["revenue_loaded", "gross_profit_loaded", "net_profit_loaded"], "next_stage": "thesis_formed"},
        "thesis_formed": {"checks": ["investment_thesis_written", "thesis_status_set", "confidence_assessed"], "next_stage": "monitoring_enabled"},
        "monitoring_enabled": {"checks": ["time_series_signals_enabled", "baseline_established", "delta_detector_active"], "next_stage": "display_ready"},
        "display_ready": {"checks": ["detail_page_generated", "homepage_card_added", "index_listed"], "next_stage": None},
    }
    return {"phase147_stage_checklist": {"stages": len(stages), "checklist": stages, "mock_used": False, "fixture_used": False}}
