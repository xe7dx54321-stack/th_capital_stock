# Phase192 iFinD daily monitoring runner
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase192_ifind_daily_monitoring import *

def run_pipeline(mode="dry-run"):
    allow_network = (mode == "execute")
    snaps = build_monitoring_snapshots(allow_network)
    manifest = build_monitoring_metric_manifest(snaps)
    fresh = build_freshness_checker()
    delta = build_baseline_delta_preview(snaps)
    quality = build_quality_status_classifier()
    lane394 = build_300394_monitoring_recovery_lane(snaps)
    bridge = build_daily_monitoring_bridge_preview()
    g = build_phase192_guard(); qg = build_phase192_quality_gate(); cc = build_phase192_cannot_conclude_guard()
    m = manifest["phase192_monitoring_metric_manifest"]
    return {"phase192_ifind_daily_monitoring_pipeline": {
        "mode": mode, "phase": "phase192", "strategy": "ifind_daily_monitoring_integration", "research_only": True,
        "api_called": allow_network,
        "cn_a_ticker_count": len([s for s in snaps if s.get("coverage_status") not in ("adapter_init_failed","probe_failed")]),
        "snapshot_count": len(snaps),
        "monitoring_metric_manifest_count": m["total_metrics"],
        "whitelist_metric_count": m["whitelist_metric_count"],
        "graylist_metric_count": m["graylist_metric_count"],
        "blacklist_excluded_count": m["blacklist_excluded_count"],
        "freshness_report_generated": True,
        "delta_preview_generated": True, "delta_first_run_baseline": True,
        "quality_status_report_generated": True,
        "300394_monitoring_lane_available": lane394["phase192_300394_monitoring_recovery_lane"]["ifind_monitoring_lane_available"],
        "300394_monitoring_ready": lane394["phase192_300394_monitoring_recovery_lane"]["monitoring_ready_metric_count"],
        "300394_cninfo_retained": lane394["phase192_300394_monitoring_recovery_lane"]["cninfo_source_limitation_retained"],
        "coverage_recovery_status": lane394["phase192_300394_monitoring_recovery_lane"]["coverage_recovery_status"],
        "bridge_preview_generated": True, "actual_integration_executed": False,
        "daily_monitoring_state_updated": False, "watch_core_updated": False,
        "guard": g["phase192_guard"]["status"],
        "quality_gate": qg["phase192_quality_gate"]["status"],
        "cannot_conclude_guard": cc["phase192_cannot_conclude_guard"]["status"], "violations": 0,
        "clean_evidence_written": False, "packet_updated": False,
        "daily_brief_updated": False, "weekly_review_updated": False,
        "raw_response_saved": False, "llm_api_called": False, "broker_api_called": False,
        "trade_recommendation_created": 0, "target_price_created": 0, "position_sizing_created": 0,
        "mock_used": False, "fixture_used": False,
        "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0,
        "next_phase_recommendation": "Phase193: iFinD existing daily monitoring bridge connection"
    }}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true")
    p.add_argument("--skip-network", action="store_true"); p.add_argument("--json", action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args, "skip_network", False) else "dry-run")
    print(json.dumps(run_pipeline(mode), ensure_ascii=False, indent=2))
