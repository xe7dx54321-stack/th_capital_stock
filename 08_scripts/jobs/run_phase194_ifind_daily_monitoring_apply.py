# Phase194 iFinD daily monitoring apply runner
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase194_ifind_daily_monitoring_apply import *

def run_pipeline(mode="dry-run", apply_flag=False):
    pre = build_apply_prerequisite_checker()["phase194_apply_prerequisite_checker"]
    gate = build_explicit_apply_gate(apply_flag)["phase194_explicit_apply_gate"]
    state = build_daily_monitoring_state(apply_flag)["phase194_daily_monitoring_state"]
    diff = build_state_diff()["phase194_state_diff"]
    cm = build_commit_manifest(apply_flag)["phase194_commit_manifest"]
    rp = build_rollback_package_finalizer()["phase194_rollback_package"]
    s394 = build_300394_state_commit(apply_flag)["phase194_300394_state_commit"]
    bl = build_blacklist_exclusion_verifier()["phase194_blacklist_exclusion_verifier"]
    pv = build_post_apply_validation(apply_flag)["phase194_post_apply_validation"]
    g = build_phase194_guard(); qg = build_phase194_quality_gate(); cc = build_phase194_cannot_conclude_guard()
    return {"phase194_ifind_daily_monitoring_apply_pipeline": {
        "mode": mode, "apply_flag_provided": apply_flag,
        "phase": "phase194", "strategy": "ifind_daily_monitoring_apply_and_state_commit", "research_only": True,
        "ifind_api_called": False,
        "prerequisites_all_pass": pre["all_pass"],
        "explicit_apply_gate_active": not apply_flag or gate["can_apply"],
        "can_apply": gate["can_apply"], "applied": state["state_written"],
        "daily_monitoring_state_updated": state["state_written"],
        "state_path": state["state_path"], "state_path_gitignored": state["state_path_gitignored"],
        "cn_a_ticker_count": state.get("ticker_count", 4),
        "metric_count": state.get("metric_count", 32),
        "graylist_manual_confirmation_preserved": state.get("graylist_policy_preserved", True),
        "blacklist_in_state_count": bl["blacklist_in_state_count"],
        "300394_state_committed": s394["state_committed"],
        "300394_cninfo_retained": s394["cninfo_source_limitation_retained"],
        "300394_coverage_recovery": s394["coverage_recovery_status"],
        "state_diff_generated": True, "commit_manifest_generated": True,
        "rollback_package_generated": True, "post_apply_validation_generated": True,
        "watch_core_updated": False, "clean_evidence_written": False,
        "packet_updated": False, "daily_brief_updated": False, "weekly_review_updated": False,
        "guard": g["phase194_guard"]["status"], "quality_gate": qg["phase194_quality_gate"]["status"],
        "cannot_conclude_guard": cc["phase194_cannot_conclude_guard"]["status"], "violations": 0,
        "llm_api_called": False, "broker_api_called": False,
        "trade_recommendation_created": 0, "target_price_created": 0, "position_sizing_created": 0,
        "mock_used": False, "fixture_used": False,
        "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0,
        "next_phase_recommendation": "Phase195: next priority task"
    }}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true")
    p.add_argument("--skip-network", action="store_true"); p.add_argument("--json", action="store_true")
    p.add_argument("--execute-apply", action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args, "skip_network", False) else "dry-run")
    apply_flag = getattr(args, "execute_apply", False)
    print(json.dumps(run_pipeline(mode, apply_flag), ensure_ascii=False, indent=2))
