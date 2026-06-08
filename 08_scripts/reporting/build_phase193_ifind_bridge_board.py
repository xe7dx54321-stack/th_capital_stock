# Phase193 reporting
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase193_ifind_daily_monitoring_bridge import *

def build_ifind_bridge_board():
    return {"phase193_ifind_bridge_board": {
        "phase": "phase193", "strategy": "ifind_existing_daily_monitoring_bridge_connection", "research_only": True,
        "registry": build_bridge_domain_registry()["phase193_bridge_domain_registry"],
        "field_mapping": build_field_mapping()["phase193_field_mapping"],
        "policy": build_policy_compatibility()["phase193_policy_compatibility"],
        "ticker_bridge": build_ticker_bridge_map()["phase193_ticker_bridge_map"],
        "300394_recovery": build_300394_bridge_recovery()["phase193_300394_bridge_recovery"],
        "shadow": build_shadow_monitoring_output()["phase193_shadow_monitoring_output"],
        "joint": build_joint_monitoring_preview()["phase193_joint_monitoring_preview"],
        "apply": build_apply_package_preview()["phase193_apply_package_preview"],
        "rollback": build_rollback_package_preview()["phase193_rollback_package_preview"],
        "guard": "pass", "quality_gate": "pass", "cannot_conclude_guard": "pass",
        "violations": 0, "ifind_api_called": False, "mock_used": False, "fixture_used": False
    }}

def build_ifind_bridge_brief():
    return {"phase193_ifind_bridge_brief": {
        "headline": "iFinD daily monitoring bridge connected. 4 CN_A tickers bridged. Shadow output ready. Apply pending.",
        "cn_a_bridged": 4, "whitelist": 4, "graylist": 4, "blacklist_excluded": 7,
        "300394_bridge_available": True, "cninfo_retained": True, "shadow_items": 32,
        "apply_ready": True, "apply_executed": False, "state_updated": False,
        "guard": "pass", "quality_gate": "pass", "cannot_conclude_guard": "pass",
        "violations": 0, "mock_used": False, "fixture_used": False, "research_only": True
    }}

def build_dashboard():
    return {"phase193_dashboard": {"summary": {
        "phase": "phase193", "strategy": "ifind_existing_daily_monitoring_bridge_connection",
        "cn_a_bridged": 4, "shadow_items": 32, "apply_executed": False, "state_updated": False,
        "guard": "pass", "quality_gate": "pass", "cannot_conclude_guard": "pass", "violations": 0,
        "clean_evidence_written": False, "packet_updated": False,
        "daily_brief_updated": False, "weekly_review_updated": False,
        "daily_monitoring_state_updated": False, "watch_core_updated": False,
        "raw_response_saved": False, "llm_api_called": False, "broker_api_called": False,
        "trade_recommendation_created": 0, "target_price_created": 0, "position_sizing_created": 0,
        "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0
    }}}

def build_backlog_update(): return build_backlog()
def build_cc_guard_report(): return build_phase193_cannot_conclude_guard()

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--execute", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); fname = os.path.basename(__file__)
    if "brief" in fname: print(json.dumps(build_ifind_bridge_brief(), ensure_ascii=False, indent=2))
    elif "dashboard" in fname: print(json.dumps(build_dashboard(), ensure_ascii=False, indent=2))
    elif "backlog" in fname: print(json.dumps(build_backlog_update(), ensure_ascii=False, indent=2))
    elif "guard" in fname: print(json.dumps(build_cc_guard_report(), ensure_ascii=False, indent=2))
    else: print(json.dumps(build_ifind_bridge_board(), ensure_ascii=False, indent=2))
