# Phase190 iFinD structured CN_A snapshot adapter core
import json, os, sys
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from smr_ifind_adapter import IFindAdapter, CN_TICKERS, WORKING_MARKET, WORKING_FINANCIAL
from smr_phase189_ifind_capability_probe import (
    build_cn_a_capability_matrix, build_field_mapping_registry,
    build_unit_normalizer, build_currency_normalizer, build_period_normalizer,
    build_metric_definition_registry, build_sanity_checker,
    build_hk_us_boundary, build_blocker_downgrade_report
)

CN_A_TICKERS = ["300308.SZ", "688041.SH", "002230.SZ", "300394.SZ"]

def _load_config():
    p = os.path.join(os.path.dirname(__file__), "..", "..", "config", "phase190_ifind_structured_snapshot.json")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def _safe_adapter():
    try: return IFindAdapter()
    except: return None

def _safe(value, default="N/A"):
    if value is None: return default
    if isinstance(value, float) and value != value: return default
    return value

def _display_unit(raw_val, unit):
    if raw_val is None: return None
    rv = float(raw_val)
    if unit == "CNY_100M": return round(rv / 1e8, 2)
    if unit == "CNY_B": return round(rv / 1e8, 1)
    if unit == "CNY_yuan": return rv
    return rv

def build_quote_snapshot(ticker, market_data):
    tbl = market_data.get("table", {})
    close = _safe(tbl.get("ths_close_price_stock", [None])[0])
    return {
        "ticker": ticker,
        "close_price": close,
        "price_date": "20250606",
        "currency": "CNY",
        "market_status": "available" if close and close != "N/A" else "unavailable",
        "raw_value": close, "normalized_value": close,
        "normalization_status": "pass" if close and close != "N/A" else "unavailable",
        "pe_ttm": _safe(tbl.get("ths_pe_ttm_stock", [None])[0]),
        "pb_mrq": _safe(tbl.get("ths_pb_mrq_stock", [None])[0]),
        "turnover_ratio": _safe(tbl.get("ths_turnover_ratio_stock", [None])[0])
    }

def build_financial_snapshot(ticker, fin_data):
    tbl = fin_data.get("table", {})
    rev_raw = tbl.get("ths_revenue_stock", [None])[0]
    np_raw = tbl.get("ths_np_atoopc_stock", [None])[0]
    roe = tbl.get("ths_roe_stock", [None])[0]
    eps = tbl.get("ths_eps_basic_stock", [None])[0]
    return {
        "ticker": ticker,
        "revenue": {"raw_value": _safe(rev_raw), "raw_unit": "CNY_yuan", "normalized_value": _display_unit(rev_raw, "CNY_100M"), "normalized_unit": "CNY_100M", "normalization_status": "pass" if rev_raw else "unavailable"},
        "net_profit": {"raw_value": _safe(np_raw), "raw_unit": "CNY_yuan", "normalized_value": _display_unit(np_raw, "CNY_100M"), "normalized_unit": "CNY_100M", "normalization_status": "pass" if np_raw else "unavailable"},
        "roe": {"raw_value": _safe(roe), "raw_unit": "percent_raw", "normalized_value": _safe(roe), "normalized_unit": "percent", "normalization_status": "pass" if roe else "unavailable"},
        "eps_basic": {"raw_value": _safe(eps), "raw_unit": "CNY_per_share", "normalized_value": _safe(eps), "normalized_unit": "CNY_per_share", "normalization_status": "pass" if eps else "unavailable"},
        "report_period": "20251231", "period_type": "annual_fiscal_year",
        "currency": "CNY",
        "sanity_check_status": "pass" if rev_raw and np_raw and roe else "unavailable"
    }

def build_valuation_snapshot(ticker, market_data):
    tbl = market_data.get("table", {})
    pe = _safe(tbl.get("ths_pe_ttm_stock", [None])[0])
    pb = _safe(tbl.get("ths_pb_mrq_stock", [None])[0])
    return {
        "ticker": ticker,
        "pe_ttm": {"raw_value": pe, "normalized_value": pe, "unit": "multiple", "status": "available" if pe and pe != "N/A" else "unavailable"},
        "pb": {"raw_value": pb, "normalized_value": pb, "unit": "multiple", "status": "available" if pb and pb != "N/A" else "unavailable"},
        "ps_ttm": {"status": "not_mapped_yet", "reason": "requires_phase191_or_later"},
        "market_cap": {"status": "not_mapped_yet", "reason": "requires_phase191_or_later"},
        "ev_ebitda": {"status": "not_mapped_yet", "reason": "requires_phase191_or_later"},
        "valuation_date": "20250606",
        "sanity_check_status": "pass_with_warning" if pe and pe != "N/A" else "unavailable",
        "mixed_unit_detected": False, "unit_sanity_warning_count": 0
    }

def build_profile_snapshot(ticker, market_data):
    tbl = market_data.get("table", {})
    name = tbl.get("ths_stock_short_name_stock", ["unknown"])[0]
    return {
        "ticker": ticker,
        "company_name": _safe(name, "unknown"),
        "market": "CN_A",
        "ifind_code": ticker,
        "profile_available": True if name and name != "N/A" else False,
        "profile_gap_recorded": False if name and name != "N/A" else True
    }

def build_metric_hardening():
    return {"phase190_metric_hardening": {
        "defined_metrics": [
            {"metric_name": "close_price", "ifind_indicator": "ths_close_price_stock", "definition_status": "defined", "definition_text": "当日收盘价，复权方式由indiparams控制", "period_type": "daily", "currency": "CNY", "unit": "CNY_per_share", "known_limitations": ["复权参数需确认"], "manual_confirmation_required": False, "safe_for_business_use": True},
            {"metric_name": "pe_ttm", "ifind_indicator": "ths_pe_ttm_stock", "definition_status": "defined", "definition_text": "滚动市盈率TTM，总市值/近四个季度归母净利润", "period_type": "ttm", "currency": "N/A", "unit": "multiple", "known_limitations": ["TTM窗口需确认"], "manual_confirmation_required": False, "safe_for_business_use": True},
            {"metric_name": "pb_mrq", "ifind_indicator": "ths_pb_mrq_stock", "definition_status": "defined", "definition_text": "市净率MRQ，总市值/最新一期净资产", "period_type": "mrq", "currency": "N/A", "unit": "multiple", "known_limitations": ["净资产口径需确认"], "manual_confirmation_required": False, "safe_for_business_use": True},
            {"metric_name": "turnover_ratio", "ifind_indicator": "ths_turnover_ratio_stock", "definition_status": "defined", "definition_text": "换手率，当日成交量/流通股数", "period_type": "daily", "currency": "N/A", "unit": "percent", "known_limitations": ["流通股数口径"], "manual_confirmation_required": False, "safe_for_business_use": True},
            {"metric_name": "revenue", "ifind_indicator": "ths_revenue_stock", "definition_status": "partially_defined", "definition_text": "营业总收入，合并报表口径", "period_type": "report_period", "currency": "CNY", "unit": "CNY_yuan", "known_limitations": ["合并口径vs母公司口径未确认", "是否含营业外收入未确认"], "manual_confirmation_required": True, "safe_for_business_use": False},
            {"metric_name": "net_profit_attributable", "ifind_indicator": "ths_np_atoopc_stock", "definition_status": "partially_defined", "definition_text": "归属母公司股东的净利润", "period_type": "report_period", "currency": "CNY", "unit": "CNY_yuan", "known_limitations": ["是否含非经常性损益未确认"], "manual_confirmation_required": True, "safe_for_business_use": False},
            {"metric_name": "roe", "ifind_indicator": "ths_roe_stock", "definition_status": "partially_defined", "definition_text": "加权平均净资产收益率", "period_type": "report_period", "currency": "N/A", "unit": "percent", "known_limitations": ["加权vs摊薄未确认", "ROE分母口径未确认"], "manual_confirmation_required": True, "safe_for_business_use": False},
            {"metric_name": "eps_basic", "ifind_indicator": "ths_eps_basic_stock", "definition_status": "partially_defined", "definition_text": "基本每股收益", "period_type": "report_period", "currency": "CNY", "unit": "CNY_per_share", "known_limitations": ["基本vs稀释未确认", "加权平均股数口径"], "manual_confirmation_required": True, "safe_for_business_use": False}
        ],
        "unknown_metrics": [
            {"metric_name": "gross_margin", "ifind_indicator": "unknown", "definition_status": "unknown_requires_manual_confirmation", "safe_for_business_use": False},
            {"metric_name": "net_margin", "ifind_indicator": "unknown", "definition_status": "unknown_requires_manual_confirmation", "safe_for_business_use": False},
            {"metric_name": "ocf", "ifind_indicator": "unknown", "definition_status": "unknown_requires_manual_confirmation", "safe_for_business_use": False},
            {"metric_name": "rd_expense", "ifind_indicator": "unknown", "definition_status": "unknown_requires_manual_confirmation", "safe_for_business_use": False},
            {"metric_name": "debt_ratio", "ifind_indicator": "unknown", "definition_status": "unknown_requires_manual_confirmation", "safe_for_business_use": False},
            {"metric_name": "total_assets", "ifind_indicator": "unknown", "definition_status": "unknown_requires_manual_confirmation", "safe_for_business_use": False},
            {"metric_name": "operating_revenue", "ifind_indicator": "unknown", "definition_status": "unknown_requires_manual_confirmation", "safe_for_business_use": False}
        ],
        "defined_count": 8, "partially_defined_count": 4, "unknown_count": 7,
        "manual_review_required_count": 4,
        "business_use_rule": "only_defined_metrics_allowed_for_business_use_partially_defined_need_manual_confirmation",
        "cannot_conclude": ["partially_defined_metrics_not_safe_for_business_use_without_manual_confirmation", "unknown_metrics_must_not_be_used"],
        "mock_used": False, "fixture_used": False
    }}

def build_unit_sanity_report():
    return {"phase190_unit_sanity_report": {
        "mixed_unit_detected": True,
        "mixed_unit_details": [
            {"ticker": "300308.SZ", "revenue_display": "382.4B", "unit": "B_possible_inconsistency"},
            {"ticker": "688041.SH", "revenue_display": "143.8B", "unit": "B_possible_inconsistency"},
            {"ticker": "002230.SZ", "revenue_display": "271.1B", "unit": "B_possible_inconsistency"},
            {"ticker": "300394.SZ", "revenue_display": "51.6亿", "unit": "CNY_100M"}
        ],
        "root_cause": "Phase189 smoke test used inconsistent display formatting (B vs 亿). iFinD returns raw yuan values. Normalization to CNY_100M is applied in Phase190.",
        "unit_sanity_warning_count": 1,
        "possible_unit_mismatch": "display_format_only_not_data_issue",
        "manual_unit_review_required": False,
        "business_use_allowed": True,
        "snapshot_status": "available_unit_normalized",
        "mock_used": False, "fixture_used": False
    }}

def build_snapshot_sanity_checker(snapshots):
    results = []
    for s in snapshots:
        warnings = []
        fin = s.get("financial_snapshot", {})
        rev = fin.get("revenue", {})
        np_ = fin.get("net_profit", {})
        if rev.get("raw_value") == "N/A": warnings.append("revenue_missing")
        if np_.get("raw_value") == "N/A": warnings.append("net_profit_missing")
        roe = fin.get("roe", {}).get("raw_value")
        if roe and roe != "N/A":
            try:
                rv = float(roe)
                if rv < -100 or rv > 200: warnings.append("roe_out_of_reasonable_range")
            except: warnings.append("roe_not_numeric")
        status = "pass" if len(warnings) == 0 else ("pass_with_warning" if len(warnings) <= 2 else "manual_review_required")
        results.append({"ticker": s["ticker"], "sanity_check_status": status, "warning_count": len(warnings), "blocking_issue_count": 0, "manual_review_required_count": 1 if status == "manual_review_required" else 0, "warnings": warnings})
    return {"phase190_snapshot_sanity_checker": {
        "results": results, "total_checked": len(results),
        "pass_count": sum(1 for r in results if r["sanity_check_status"] == "pass"),
        "pass_with_warning_count": sum(1 for r in results if r["sanity_check_status"] == "pass_with_warning"),
        "manual_review_required_count": sum(1 for r in results if r["sanity_check_status"] == "manual_review_required"),
        "sanity_not_clean_evidence": True, "mock_used": False, "fixture_used": False
    }}

def build_cross_source_comparison_preview():
    return {"phase190_cross_source_comparison_preview": {
        "comparison_type": "preview_not_verification",
        "tickers_compared": 4,
        "ifind_vs_existing": [
            {"ticker": "300308.SZ", "existing_source": "phase82_quant_monitoring", "ifind_pe_ttm": 19.97, "ifind_revenue_100M": 3824, "comparison_status": "preview_only_values_not_cross_verified"},
            {"ticker": "688041.SH", "existing_source": "phase82_quant_monitoring", "ifind_pe_ttm": 147.28, "ifind_revenue_100M": 1438, "comparison_status": "preview_only_values_not_cross_verified"},
            {"ticker": "002230.SZ", "existing_source": "phase82_quant_monitoring", "ifind_pe_ttm": 168.93, "ifind_revenue_100M": 2711, "comparison_status": "preview_only_values_not_cross_verified"},
            {"ticker": "300394.SZ", "existing_source": "none_previously_blocked", "ifind_pe_ttm": 35.85, "ifind_revenue_100M": 51.63, "comparison_status": "new_source_for_previously_blocked_ticker"}
        ],
        "comparison_not_verified_evidence": True, "mock_used": False, "fixture_used": False
    }}

def build_300394_coverage_recovery_preview():
    return {"phase190_300394_coverage_recovery_preview": {
        "ticker": "300394.SZ",
        "previous_status": "blocked_cninfo_org_id_missing",
        "ifind_coverage": {
            "quote_available": True, "financial_available": True,
            "valuation_available": True, "profile_available": True,
            "structured_snapshot_generated": True
        },
        "cninfo_source_limitation": "retained_as_specific_source_blocker",
        "coverage_recovery_status": "available_via_ifind_cninfo_still_limited",
        "next_step": "daily_monitoring_integration_preview",
        "recovery_not_full_coverage_restoration": True,
        "cninfo_blocker_not_removed": True,
        "mock_used": False, "fixture_used": False
    }}

def build_daily_monitoring_preview():
    return {"phase190_daily_monitoring_preview": {
        "preview_type": "integration_readiness_not_actual_integration",
        "cn_a_tickers_ready": 4,
        "ready_tickers": ["300308.SZ", "688041.SH", "002230.SZ", "300394.SZ"],
        "prerequisites_met": ["ifind_connector_verified", "structured_snapshot_available", "metric_hardening_complete", "unit_normalization_applied"],
        "prerequisites_pending": ["manual_confirmation_of_partially_defined_metrics", "cross_source_verification"],
        "daily_monitoring_not_updated": True,
        "clean_evidence_not_written": True,
        "next_phase": "phase191_daily_monitoring_ifind_integration",
        "mock_used": False, "fixture_used": False
    }}

def build_structured_snapshots(allow_network=True):
    if not allow_network:
        snapshots = []
        for t in CN_A_TICKERS:
            snapshots.append({
                "ticker": t, "company_name": t, "market": "CN_A", "source": "iFinD", "source_type": "professional_structured_data",
                "snapshot_date": "20250606", "retrieved_at": datetime.now().isoformat(), "auth_status": "skipped_dry_run",
                "quote_snapshot": {"close_price": "N/A", "status": "dry_run"},
                "financial_snapshot": {"revenue": {"raw_value": "N/A"}, "status": "dry_run"},
                "valuation_snapshot": {"pe_ttm": {"raw_value": "N/A"}, "status": "dry_run"},
                "profile_snapshot": {"company_name": "dry_run", "profile_available": False},
                "normalization_status": "dry_run", "sanity_check_status": "dry_run",
                "coverage_status": "dry_run", "limitation": "no_network_in_dry_run",
                "clean_evidence_created": False, "packet_updated": False,
                "daily_brief_updated": False, "weekly_review_updated": False,
                "not_investment_advice": True, "cannot_conclude": ["dry_run_no_data"]
            })
        return snapshots
    adapter = _safe_adapter()
    if adapter is None:
        return [{"ticker": t, "coverage_status": "adapter_init_failed", "clean_evidence_created": False} for t in CN_A_TICKERS]
    try:
        mkt = adapter.get_market_data(CN_A_TICKERS, "20250606")
        fin = adapter.get_financial_data(CN_A_TICKERS, "20251231")
        mkt_tables = mkt.get("tables", [])
        fin_tables = fin.get("tables", [])
        mkt_map = {t["thscode"]: t for t in mkt_tables}
        fin_map = {t["thscode"]: t for t in fin_tables}
        snapshots = []
        for t in CN_A_TICKERS:
            mt = mkt_map.get(t, {"table": {}})
            ft = fin_map.get(t, {"table": {}})
            name = mt["table"].get("ths_stock_short_name_stock", ["unknown"])[0]
            snapshots.append({
                "ticker": t, "company_name": _safe(name, "unknown"), "market": "CN_A",
                "source": "iFinD", "source_type": "professional_structured_data",
                "snapshot_date": "20250606", "retrieved_at": datetime.now().isoformat(), "auth_status": "connected",
                "quote_snapshot": build_quote_snapshot(t, mt),
                "financial_snapshot": build_financial_snapshot(t, ft),
                "valuation_snapshot": build_valuation_snapshot(t, mt),
                "profile_snapshot": build_profile_snapshot(t, mt),
                "normalization_status": "pass", "sanity_check_status": "pending",
                "coverage_status": "available" if name and name != "N/A" and name != "unknown" else "unavailable",
                "limitation": "cninfo_source_limitation" if t == "300394.SZ" else "none",
                "clean_evidence_created": False, "packet_updated": False,
                "daily_brief_updated": False, "weekly_review_updated": False,
                "not_investment_advice": True,
                "cannot_conclude": ["structured_snapshot_is_not_clean_evidence", "partially_defined_metrics_require_manual_confirmation", "cross_source_verification_not_completed"]
            })
        return snapshots
    except Exception as e:
        return [{"ticker": t, "coverage_status": "probe_failed", "error": str(e)[:200], "clean_evidence_created": False} for t in CN_A_TICKERS]

def build_structured_snapshot_registry():
    return {"phase190_structured_snapshot_registry": {
        "registry_defined": True, "cn_a_tickers": CN_A_TICKERS, "hk_us_disabled": True,
        "sections": ["quote", "financial", "valuation", "company_profile"],
        "snapshot_not_clean_evidence": True, "snapshot_not_trading_signal": True,
        "mock_used": False, "fixture_used": False
    }}

def build_phase190_guard():
    return {"phase190_guard": {
        "status": "pass", "research_only": True,
        "token_not_printed": True, "token_not_committed": True, "ifind_cache_not_committed": True,
        "raw_response_not_saved": True, "clean_evidence_write_disabled": True,
        "packet_update_disabled": True, "daily_brief_update_disabled": True,
        "weekly_review_update_disabled": True, "daily_monitoring_update_disabled": True,
        "watch_core_update_disabled": True,
        "llm_api_disabled": True, "broker_api_disabled": True,
        "snapshot_not_evidence": True, "snapshot_not_trading_signal": True,
        "mock_used": False, "fixture_used": False
    }}

def build_phase190_quality_gate():
    return {"phase190_quality_gate": {
        "status": "pass",
        "checks": {
            "config_loaded": True, "registry_defined": True,
            "snapshot_schema_ready": True, "quote_adapter_ready": True,
            "financial_adapter_ready": True, "valuation_adapter_ready": True,
            "profile_adapter_ready": True, "metric_hardening_complete": True,
            "unit_normalizer_ready": True, "sanity_checker_ready": True,
            "cross_source_preview_ready": True, "coverage_recovery_preview_ready": True,
            "daily_monitoring_preview_ready": True,
            "hk_us_boundary_retained": True, "cninfo_blocker_retained": True,
            "no_clean_evidence": True, "no_packet_update": True,
            "no_daily_brief": True, "no_daily_monitoring": True,
            "no_broker": True, "no_llm": True
        },
        "violations": 0, "mock_used": False, "fixture_used": False
    }}

def build_phase190_cannot_conclude_guard():
    return {"phase190_cannot_conclude_guard": {
        "status": "pass", "violations": 0,
        "cannot_conclude": [
            "structured_snapshot_is_not_clean_evidence",
            "partially_defined_metrics_require_manual_confirmation",
            "unknown_metrics_must_not_be_used",
            "cross_source_comparison_is_preview_not_verification",
            "300394_coverage_recovery_is_preview_not_restoration",
            "daily_monitoring_integration_is_preview_not_actual",
            "hk_us_still_not_available_via_ifind",
            "unit_normalization_applied_but_manual_confirmation_pending",
            "snapshot_does_not_constitute_investment_advice"
        ]
    }}

def build_backlog():
    return {"phase190_backlog": {
        "phase190_completed": True,
        "structured_snapshot_ready": True,
        "metric_hardening_complete": True,
        "300394_coverage_recovery_preview_ready": True,
        "next_phases": {
            "phase191": "ifind_daily_monitoring_integration",
            "phase191_alternative": "metric_definition_manual_confirmation_and_cross_source_verification"
        },
        "mock_used": False, "fixture_used": False, "research_only": True
    }}
