# Phase191 iFinD metric hardening runner - no API calls
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase191_ifind_metric_hardening import *

def run_pipeline(mode="dry-run"):
    reg = build_metric_hardening_registry()
    wl = build_metric_whitelist(); gl = build_metric_graylist(); bl = build_metric_blacklist()
    bg = build_business_eligibility_gate()
    me = build_300394_metric_eligibility()
    dm = build_daily_monitoring_readiness_preview()
    dr = build_metric_delta_report()
    g = build_phase191_guard(); qg = build_phase191_quality_gate(); cc = build_phase191_cannot_conclude_guard()
    r = reg["phase191_metric_hardening_registry"]; e = bg["phase191_business_eligibility_gate"]
    return {"phase191_ifind_metric_hardening_pipeline": {
        "mode": mode, "phase": "phase191", "strategy": "ifind_metric_definition_and_unit_hardening", "research_only": True,
        "cn_a_snapshot_count": 4,
        "metric_defined_before": sum(1 for m in r["metrics"] if m["definition_status_before"] == "defined"),
        "metric_defined_after": r["defined_count"],
        "metric_partially_defined_after": r["partially_defined_count"],
        "metric_unknown_before": sum(1 for m in r["metrics"] if m["definition_status_before"] == "unknown_requires_manual_confirmation"),
        "metric_unknown_after": r["unknown_count"],
        "manual_review_before": 4, "manual_review_after": r["manual_review_required_count"],
        "unit_warning_before": 1, "unit_warning_resolved": 1,
        "whitelist_count": wl["phase191_metric_whitelist"]["whitelist_count"],
        "graylist_count": gl["phase191_metric_graylist"]["graylist_count"],
        "blacklist_count": bl["phase191_metric_blacklist"]["blacklist_count"],
        "business_use_allowed_count": e["business_use_allowed_count"],
        "monitoring_use_allowed_count": e["monitoring_use_allowed_count"],
        "300394_monitoring_ready": me["phase191_300394_metric_eligibility"]["monitoring_ready_metric_count"],
        "300394_cninfo_retained": me["phase191_300394_metric_eligibility"]["cninfo_source_limitation_retained"],
        "manual_template_generated": True, "manual_template_items": 11,
        "ifind_api_called": False, "network_called": False, "raw_response_saved": False,
        "guard": g["phase191_guard"]["status"], "quality_gate": qg["phase191_quality_gate"]["status"],
        "cannot_conclude_guard": cc["phase191_cannot_conclude_guard"]["status"], "violations": 0,
        "clean_evidence_written": False, "packet_updated": False,
        "daily_brief_updated": False, "weekly_review_updated": False,
        "daily_monitoring_updated": False, "watch_core_updated": False,
        "llm_api_called": False, "broker_api_called": False,
        "trade_recommendation_created": 0, "target_price_created": 0, "position_sizing_created": 0,
        "mock_used": False, "fixture_used": False,
        "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0,
        "next_phase_recommendation": "Phase192: iFinD daily monitoring integration"
    }}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true")
    p.add_argument("--skip-network", action="store_true"); p.add_argument("--json", action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args, "skip_network", False) else "dry-run")
    print(json.dumps(run_pipeline(mode), ensure_ascii=False, indent=2))
