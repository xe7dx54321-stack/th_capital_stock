# Phase193 iFinD daily monitoring bridge runner - no API calls
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase193_ifind_daily_monitoring_bridge import *

def run_pipeline(mode="dry-run"):
    fm = build_field_mapping()["phase193_field_mapping"]
    pol = build_policy_compatibility()["phase193_policy_compatibility"]
    tb = build_ticker_bridge_map()["phase193_ticker_bridge_map"]
    br = build_300394_bridge_recovery()["phase193_300394_bridge_recovery"]
    sh = build_shadow_monitoring_output()["phase193_shadow_monitoring_output"]
    jt = build_joint_monitoring_preview()["phase193_joint_monitoring_preview"]
    ap = build_apply_package_preview()["phase193_apply_package_preview"]
    g = build_phase193_guard(); qg = build_phase193_quality_gate(); cc = build_phase193_cannot_conclude_guard()
    return {"phase193_ifind_daily_monitoring_bridge_pipeline": {
        "mode": mode, "phase": "phase193", "strategy": "ifind_existing_daily_monitoring_bridge_connection", "research_only": True,
        "ifind_api_called": False,
        "cn_a_ticker_count": tb["ticker_count"], "field_mapping_count": fm["total"],
        "policy_compatible": pol["compatible_metric_count"], "manual_confirmation": pol["manual_confirmation_metric_count"],
        "blacklist_excluded": pol["blocked_metric_count"],
        "300394_bridge_available": br["bridge_available"],
        "300394_cninfo_retained": br["cninfo_source_limitation_retained"],
        "300394_coverage_recovery_bridge": br["coverage_recovery_bridge_status"],
        "shadow_output_generated": True, "shadow_item_count": sh["shadow_item_count"],
        "joint_preview_generated": True, "conflict_detected_count": jt["conflict_detected_count"],
        "overwrite_allowed": False, "apply_package_generated": True, "apply_executed": False,
        "rollback_package_generated": True,
        "actual_daily_monitoring_state_updated": False, "watch_core_updated": False,
        "guard": g["phase193_guard"]["status"], "quality_gate": qg["phase193_quality_gate"]["status"],
        "cannot_conclude_guard": cc["phase193_cannot_conclude_guard"]["status"], "violations": 0,
        "clean_evidence_written": False, "packet_updated": False,
        "daily_brief_updated": False, "weekly_review_updated": False,
        "raw_response_saved": False, "llm_api_called": False, "broker_api_called": False,
        "trade_recommendation_created": 0, "target_price_created": 0, "position_sizing_created": 0,
        "mock_used": False, "fixture_used": False,
        "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0,
        "next_phase_recommendation": "Phase194: iFinD daily monitoring apply and state commit"
    }}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true")
    p.add_argument("--skip-network", action="store_true"); p.add_argument("--json", action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args, "skip_network", False) else "dry-run")
    print(json.dumps(run_pipeline(mode), ensure_ascii=False, indent=2))
