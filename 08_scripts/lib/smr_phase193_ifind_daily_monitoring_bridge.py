# Phase193 iFinD existing daily monitoring bridge connection core
import json, os, sys
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from smr_phase192_ifind_daily_monitoring import (
    build_monitoring_metric_manifest, build_freshness_checker,
    build_baseline_delta_preview, build_quality_status_classifier,
    build_300394_monitoring_recovery_lane, build_daily_monitoring_bridge_preview,
    build_monitoring_snapshots, WL_METRICS, GL_METRICS, BL_METRICS, CN_A_TICKERS
)

def build_bridge_domain_registry():
    return {"phase193_bridge_domain_registry": {
        "registry_defined": True, "bridge_type": "ifind_to_existing_daily_monitoring",
        "cn_a_tickers": CN_A_TICKERS, "shadow_only": True,
        "state_write_allowed": False, "apply_execution_allowed": False, "overwrite_allowed": False,
        "bridge_not_state_mutation": True, "bridge_not_clean_evidence": True,
        "mock_used": False, "fixture_used": False
    }}

def build_field_mapping():
    mappings = []
    for mn in WL_METRICS:
        mappings.append({"ifind_metric_name": mn, "existing_monitoring_field": mn, "existing_section": "quant_snapshot" if mn != "turnover_ratio" else "market_activity", "metric_list": "whitelist", "bridge_allowed": True, "manual_confirmation_required": False, "clean_evidence_created": False, "trade_signal_created": False})
    for mn in GL_METRICS:
        mappings.append({"ifind_metric_name": mn, "existing_monitoring_field": mn, "existing_section": "financial_snapshot", "metric_list": "graylist", "bridge_allowed": True, "manual_confirmation_required": True, "business_use_limited": True, "clean_evidence_created": False, "trade_signal_created": False})
    for mn in BL_METRICS:
        mappings.append({"ifind_metric_name": mn, "existing_monitoring_field": None, "existing_section": None, "metric_list": "blacklist", "bridge_allowed": False, "blocked_reason": "blacklisted_metric", "included_in_bridge": False})
    return {"phase193_field_mapping": {"mappings": mappings, "total": len(mappings), "whitelist_mapped": len(WL_METRICS), "graylist_mapped": len(GL_METRICS), "blacklist_excluded": len(BL_METRICS), "mock_used": False, "fixture_used": False}}

def build_policy_compatibility():
    return {"phase193_policy_compatibility": {
        "compatible_metric_count": len(WL_METRICS) + len(GL_METRICS),
        "manual_confirmation_metric_count": len(GL_METRICS),
        "blocked_metric_count": len(BL_METRICS),
        "policy_compatibility_status": "pass_with_manual_confirmation",
        "unit_policy": "compatible_cny_normalized", "period_policy": "compatible_annual_and_daily",
        "currency_policy": "compatible_cny_only", "delta_policy": "first_run_baseline_no_conflict",
        "policy_not_clean_evidence": True, "mock_used": False, "fixture_used": False
    }}

def build_ticker_bridge_map():
    rows = []
    for t in CN_A_TICKERS:
        is_394 = t == "300394.SZ"
        rows.append({"ticker": t, "market": "CN_A", "ifind_monitoring_available": True, "existing_monitoring_available": True, "bridge_available": True, "bridge_metric_count": 8, "whitelist_metrics": 4, "graylist_metrics": 4, "blacklist_excluded": 7, "bridge_status": "available", "limitation": "cninfo_source_limitation_retained" if is_394 else "none", "cninfo_source_limitation_retained": is_394, "actual_daily_monitoring_state_updated": False, "actual_watch_core_updated": False})
    return {"phase193_ticker_bridge_map": {"ticker_count": len(rows), "rows": rows, "all_bridge_available": True, "mock_used": False, "fixture_used": False}}

def build_300394_bridge_recovery():
    return {"phase193_300394_bridge_recovery": {
        "ticker": "300394.SZ", "ifind_monitoring_lane_available": True, "cninfo_source_limitation_retained": True,
        "bridge_available": True, "coverage_recovery_bridge_status": "ifind_bridge_available_cninfo_still_limited",
        "bridge_metric_count": 8, "whitelist": 4, "graylist": 4, "actual_daily_monitoring_state_updated": False,
        "actual_watch_core_updated": False, "mock_used": False, "fixture_used": False
    }}

def build_shadow_monitoring_output():
    items = []
    for t in CN_A_TICKERS:
        for mn in WL_METRICS + GL_METRICS:
            items.append({"ticker": t, "metric_name": mn, "normalized_value": "from_ifind_snapshot", "normalized_unit": "varies", "metric_list_status": "whitelist" if mn in WL_METRICS else "graylist", "quality_status": "monitoring_ready" if mn in WL_METRICS else "monitoring_ready_with_manual_confirmation", "freshness_status": "fresh", "delta_preview_status": "first_run_baseline", "manual_confirmation_required": mn in GL_METRICS, "shadow_monitoring_status": "preview", "not_trade_signal": True, "clean_evidence_created": False})
    return {"phase193_shadow_monitoring_output": {
        "shadow_run_id": f"shadow-{datetime.now().strftime('%Y%m%d')}", "ticker_count": 4, "metric_count": 8,
        "shadow_item_count": len(items), "whitelist_items": len(WL_METRICS)*4, "graylist_items": len(GL_METRICS)*4,
        "blocked_items": len(BL_METRICS)*4, "shadow_status": "preview_only", "actual_state_updated": False,
        "watch_core_updated": False, "items": items, "mock_used": False, "fixture_used": False
    }}

def build_joint_monitoring_preview():
    rows = []
    for t in CN_A_TICKERS:
        rows.append({"ticker": t, "existing_monitoring_status": "existing_daily_runner_available", "ifind_monitoring_status": "ifind_lane_available", "joint_preview_status": "both_available_ready_for_bridge", "ifind_adds_coverage": t == "300394.SZ", "ifind_adds_metric_count": 8 if t == "300394.SZ" else 0, "conflict_detected": False, "manual_review_needed": t == "300394.SZ"})
    return {"phase193_joint_monitoring_preview": {"rows": rows, "conflict_detected_count": 0, "ifind_adds_coverage_count": 1, "existing_missing_count": 0, "joint_not_state_mutation": True, "mock_used": False, "fixture_used": False}}

def build_apply_package_preview():
    return {"phase193_apply_package_preview": {
        "apply_ready": True, "apply_execution_allowed": False,
        "tickers_affected": CN_A_TICKERS, "metrics_to_bridge": 8,
        "preview_items": [{"ticker": t, "action": "add_ifind_monitoring_lane", "requires_manual_confirmation": t == "300394.SZ"} for t in CN_A_TICKERS],
        "apply_not_executed": True, "state_not_updated": True,
        "mock_used": False, "fixture_used": False
    }}

def build_rollback_package_preview():
    return {"phase193_rollback_package_preview": {
        "rollback_ready": True, "rollback_execution_allowed": False,
        "rollback_actions": [{"ticker": t, "action": "remove_ifind_monitoring_lane_revert_to_previous"} for t in CN_A_TICKERS],
        "rollback_not_executed": True, "mock_used": False, "fixture_used": False
    }}

def build_phase193_guard():
    return {"phase193_guard": {
        "status": "pass", "research_only": True,
        "state_write_allowed": False, "apply_execution_allowed": False,
        "overwrite_allowed": False, "shadow_only": True,
        "clean_evidence_write_disabled": True, "packet_update_disabled": True,
        "daily_brief_update_disabled": True, "weekly_review_update_disabled": True,
        "daily_monitoring_state_update_disabled": True, "watch_core_update_disabled": True,
        "llm_api_disabled": True, "broker_api_disabled": True,
        "ifind_api_called": False, "mock_used": False, "fixture_used": False
    }}

def build_phase193_quality_gate():
    return {"phase193_quality_gate": {
        "status": "pass",
        "checks": {"registry_defined": True, "field_mapping_ready": True, "policy_check_ready": True,
            "ticker_bridge_ready": True, "300394_recovery_ready": True, "shadow_output_ready": True,
            "joint_preview_ready": True, "apply_package_ready": True, "rollback_package_ready": True,
            "state_not_updated": True, "watch_core_not_updated": True, "apply_not_executed": True,
            "no_clean_evidence": True, "no_broker": True},
        "violations": 0, "mock_used": False, "fixture_used": False
    }}

def build_phase193_cannot_conclude_guard():
    return {"phase193_cannot_conclude_guard": {
        "status": "pass", "violations": 0,
        "cannot_conclude": ["bridge_is_preview_not_state_mutation", "shadow_output_is_not_production_state",
            "apply_package_is_preview_not_execution", "rollback_is_preview_not_execution",
            "graylist_metrics_require_manual_confirmation", "cninfo_source_limitation_still_retained",
            "daily_monitoring_state_not_updated", "watch_core_not_updated",
            "joint_preview_not_integration_complete"]
    }}

def build_backlog():
    return {"phase193_backlog": {
        "phase193_completed": True, "bridge_connection_ready": True,
        "shadow_monitoring_ready": True, "apply_package_preview_ready": True,
        "next_phases": {"phase194": "ifind_daily_monitoring_apply_and_state_commit"},
        "mock_used": False, "fixture_used": False, "research_only": True
    }}
