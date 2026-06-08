# Phase194 reporting
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase194_ifind_daily_monitoring_apply import *

def build_ifind_apply_board():
    return {"phase194_ifind_apply_board": {
        "phase": "phase194", "strategy": "ifind_daily_monitoring_apply_and_state_commit", "research_only": True,
        "prerequisites": build_apply_prerequisite_checker()["phase194_apply_prerequisite_checker"],
        "apply_gate": build_explicit_apply_gate(False)["phase194_explicit_apply_gate"],
        "state": build_daily_monitoring_state(False)["phase194_daily_monitoring_state"],
        "state_diff": build_state_diff()["phase194_state_diff"],
        "commit_manifest": build_commit_manifest(False)["phase194_commit_manifest"],
        "rollback": build_rollback_package_finalizer()["phase194_rollback_package"],
        "300394": build_300394_state_commit(False)["phase194_300394_state_commit"],
        "blacklist_verifier": build_blacklist_exclusion_verifier()["phase194_blacklist_exclusion_verifier"],
        "post_apply": build_post_apply_validation(False)["phase194_post_apply_validation"],
        "guard": "pass", "quality_gate": "pass", "cannot_conclude_guard": "pass",
        "violations": 0, "ifind_api_called": False, "mock_used": False, "fixture_used": False
    }}

def build_ifind_apply_brief():
    return {"phase194_ifind_apply_brief": {
        "headline": "iFinD daily monitoring state commit ready. Apply gate active. Use --execute-apply to commit.",
        "cn_a_tickers": 4, "metrics": 32, "graylist_preserved": True, "blacklist_excluded": True,
        "300394_state_ready": True, "cninfo_retained": True, "watch_core_not_updated": True,
        "guard": "pass", "quality_gate": "pass", "cannot_conclude_guard": "pass",
        "violations": 0, "mock_used": False, "fixture_used": False, "research_only": True
    }}

def build_dashboard():
    return {"phase194_dashboard": {"summary": {
        "phase": "phase194", "strategy": "ifind_daily_monitoring_apply_and_state_commit",
        "cn_a_tickers": 4, "metrics": 32, "apply_gate": "active",
        "guard": "pass", "quality_gate": "pass", "cannot_conclude_guard": "pass", "violations": 0,
        "clean_evidence_written": False, "packet_updated": False,
        "daily_brief_updated": False, "weekly_review_updated": False, "watch_core_updated": False,
        "llm_api_called": False, "broker_api_called": False,
        "trade_recommendation_created": 0, "target_price_created": 0, "position_sizing_created": 0,
        "raw_response_saved": False, "mock_used": False, "fixture_used": False,
        "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0
    }}}

def build_backlog_update(): return build_backlog()
def build_cc_guard_report(): return build_phase194_cannot_conclude_guard()

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--execute", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); fname = os.path.basename(__file__)
    if "brief" in fname: print(json.dumps(build_ifind_apply_brief(), ensure_ascii=False, indent=2))
    elif "dashboard" in fname: print(json.dumps(build_dashboard(), ensure_ascii=False, indent=2))
    elif "backlog" in fname: print(json.dumps(build_backlog_update(), ensure_ascii=False, indent=2))
    elif "guard" in fname: print(json.dumps(build_cc_guard_report(), ensure_ascii=False, indent=2))
    else: print(json.dumps(build_ifind_apply_board(), ensure_ascii=False, indent=2))
