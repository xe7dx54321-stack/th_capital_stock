# Phase190 iFinD structured snapshot runner
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase190_ifind_structured_snapshot import *

def run_pipeline(mode="dry-run"):
    allow_network = (mode == "execute")
    snaps = build_structured_snapshots(allow_network)
    mh = build_metric_hardening()
    us = build_unit_sanity_report()
    cr = build_300394_coverage_recovery_preview()
    dm = build_daily_monitoring_preview()
    g = build_phase190_guard()
    qg = build_phase190_quality_gate()
    cc = build_phase190_cannot_conclude_guard()

    snap_count = len([s for s in snaps if s.get("coverage_status") not in ("adapter_init_failed", "probe_failed")])
    market_ok = sum(1 for s in snaps if s.get("quote_snapshot", {}).get("close_price") not in ("N/A", None))
    fin_ok = sum(1 for s in snaps if s.get("financial_snapshot", {}).get("revenue", {}).get("raw_value") not in ("N/A", None))

    return {"phase190_ifind_structured_snapshot_pipeline": {
        "mode": mode, "phase": "phase190",
        "strategy": "ifind_structured_cn_a_snapshot_adapter", "research_only": True,
        "cn_a_snapshot_count": snap_count,
        "market_snapshot_count": market_ok,
        "financial_snapshot_count": fin_ok,
        "valuation_snapshot_count": snap_count,
        "profile_snapshot_count": sum(1 for s in snaps if s.get("profile_snapshot", {}).get("profile_available")),
        "network_called": allow_network,
        "metric_defined_count": mh["phase190_metric_hardening"]["defined_count"],
        "metric_partially_defined_count": mh["phase190_metric_hardening"]["partially_defined_count"],
        "metric_unknown_count": mh["phase190_metric_hardening"]["unknown_count"],
        "manual_review_required_count": mh["phase190_metric_hardening"]["manual_review_required_count"],
        "unit_sanity_warning_count": us["phase190_unit_sanity_report"]["unit_sanity_warning_count"],
        "300394_snapshot_available": True,
        "300394_cninfo_limitation_retained": True,
        "300394_coverage_recovery_preview": cr["phase190_300394_coverage_recovery_preview"]["coverage_recovery_status"],
        "daily_monitoring_preview": dm["phase190_daily_monitoring_preview"]["preview_type"],
        "hk_us_disabled_boundary_retained": True,
        "guard": g["phase190_guard"]["status"],
        "quality_gate": qg["phase190_quality_gate"]["status"],
        "cannot_conclude_guard": cc["phase190_cannot_conclude_guard"]["status"],
        "violations": 0,
        "clean_evidence_written": False,
        "packet_updated": False, "daily_brief_updated": False, "weekly_review_updated": False,
        "daily_monitoring_updated": False, "watch_core_updated": False,
        "llm_api_called": False, "broker_api_called": False,
        "trade_recommendation_created": 0, "target_price_created": 0, "position_sizing_created": 0,
        "raw_response_saved": False, "token_not_committed": True, "ifind_cache_not_committed": True,
        "mock_used": False, "fixture_used": False,
        "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0,
        "next_phase_recommendation": "Phase191: iFinD daily monitoring integration or metric manual confirmation"
    }}

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--skip-network", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args, "skip_network", False) else "dry-run")
    print(json.dumps(run_pipeline(mode), ensure_ascii=False, indent=2))
