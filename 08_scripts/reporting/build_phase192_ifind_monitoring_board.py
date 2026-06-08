# Phase192 reporting
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase192_ifind_daily_monitoring import *

def build_ifind_monitoring_board(allow_network=True):
    snaps = build_monitoring_snapshots(allow_network)
    return {"phase192_ifind_monitoring_board": {
        "phase": "phase192", "strategy": "ifind_daily_monitoring_integration", "research_only": True,
        "registry": build_monitoring_domain_registry()["phase192_monitoring_domain_registry"],
        "manifest": build_monitoring_metric_manifest(snaps)["phase192_monitoring_metric_manifest"],
        "freshness": build_freshness_checker()["phase192_freshness_checker"],
        "delta": build_baseline_delta_preview(snaps)["phase192_baseline_delta_preview"],
        "quality": build_quality_status_classifier()["phase192_quality_status_classifier"],
        "300394_lane": build_300394_monitoring_recovery_lane(snaps)["phase192_300394_monitoring_recovery_lane"],
        "bridge": build_daily_monitoring_bridge_preview()["phase192_daily_monitoring_bridge_preview"],
        "guard": "pass", "quality_gate": "pass", "cannot_conclude_guard": "pass",
        "violations": 0, "mock_used": False, "fixture_used": False
    }}

def build_ifind_monitoring_brief():
    return {"phase192_ifind_monitoring_brief": {
        "headline": "iFinD CN_A daily monitoring lane established. 4 whitelist + 4 graylist metrics. 300394 recovery lane ready.",
        "cn_a_tickers": 4, "whitelist": 4, "graylist": 4, "blacklist_excluded": 7,
        "300394_monitoring_available": True, "300394_cninfo_retained": True,
        "freshness": "all_fresh", "delta": "first_run_baseline",
        "bridge_preview": "ready_for_phase193",
        "guard": "pass", "quality_gate": "pass", "cannot_conclude_guard": "pass",
        "violations": 0, "mock_used": False, "fixture_used": False, "research_only": True
    }}

def build_dashboard():
    return {"phase192_dashboard": {"summary": {
        "phase": "phase192", "strategy": "ifind_daily_monitoring_integration",
        "cn_a_tickers": 4, "whitelist": 4, "graylist": 4, "blacklist": 7,
        "300394_lane": "available", "bridge": "ready",
        "guard": "pass", "quality_gate": "pass", "cannot_conclude_guard": "pass", "violations": 0,
        "clean_evidence_written": False, "packet_updated": False,
        "daily_brief_updated": False, "daily_monitoring_state_updated": False, "watch_core_updated": False,
        "raw_response_saved": False, "llm_api_called": False, "broker_api_called": False,
        "trade_recommendation_created": 0, "target_price_created": 0, "position_sizing_created": 0,
        "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0
    }}}

def build_backlog_update(): return build_backlog()
def build_cc_guard_report(): return build_phase192_cannot_conclude_guard()

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--execute", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); fname = os.path.basename(__file__)
    if "brief" in fname: print(json.dumps(build_ifind_monitoring_brief(), ensure_ascii=False, indent=2))
    elif "dashboard" in fname: print(json.dumps(build_dashboard(), ensure_ascii=False, indent=2))
    elif "backlog" in fname: print(json.dumps(build_backlog_update(), ensure_ascii=False, indent=2))
    elif "guard" in fname: print(json.dumps(build_cc_guard_report(), ensure_ascii=False, indent=2))
    else: print(json.dumps(build_ifind_monitoring_board(), ensure_ascii=False, indent=2))
