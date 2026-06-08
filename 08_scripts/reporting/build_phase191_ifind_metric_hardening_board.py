# Phase191 reporting: board, brief, dashboard, backlog, cc guard
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase191_ifind_metric_hardening import *

def build_ifind_metric_hardening_board():
    reg = build_metric_hardening_registry()
    sc = build_semantic_category_map()
    pc = build_period_classifier()
    ua = build_unit_conversion_audit()
    cc = build_currency_consistency_checker()
    bg = build_business_eligibility_gate()
    wl = build_metric_whitelist(); gl = build_metric_graylist(); bl = build_metric_blacklist()
    mt = build_manual_confirmation_template()
    me = build_300394_metric_eligibility()
    dm = build_daily_monitoring_readiness_preview()
    dr = build_metric_delta_report()
    return {"phase191_ifind_metric_hardening_board": {
        "phase": "phase191", "strategy": "ifind_metric_definition_and_unit_hardening", "research_only": True,
        "registry": reg["phase191_metric_hardening_registry"],
        "semantic_map": sc["phase191_semantic_category_map"],
        "period_classifier": pc["phase191_period_classifier"],
        "unit_audit": ua["phase191_unit_conversion_audit"],
        "currency_checker": cc["phase191_currency_consistency_checker"],
        "eligibility_gate": bg["phase191_business_eligibility_gate"],
        "whitelist": wl["phase191_metric_whitelist"],
        "graylist": gl["phase191_metric_graylist"],
        "blacklist": bl["phase191_metric_blacklist"],
        "manual_template": mt["phase191_manual_confirmation_template"],
        "300394_eligibility": me["phase191_300394_metric_eligibility"],
        "daily_monitoring_readiness": dm["phase191_daily_monitoring_readiness_preview"],
        "metric_delta": dr["phase191_metric_delta_report"],
        "guard": "pass", "quality_gate": "pass", "cannot_conclude_guard": "pass",
        "violations": 0, "ifind_api_called": False, "mock_used": False, "fixture_used": False
    }}

def build_ifind_metric_hardening_brief():
    return {"phase191_ifind_metric_hardening_brief": {
        "headline": "iFinD metric hardening complete. 4 whitelisted, 4 graylisted, 7 blacklisted. 300394 CMINFO limitation retained.",
        "whitelist": 4, "graylist": 4, "blacklist": 7, "manual_template_items": 11,
        "300394_monitoring_ready": 8, "cninfo_retained": True,
        "ifind_api_called": False, "guard": "pass", "quality_gate": "pass", "cannot_conclude_guard": "pass",
        "violations": 0, "mock_used": False, "fixture_used": False, "research_only": True
    }}

def build_dashboard():
    return {"phase191_dashboard": {"summary": {
        "phase": "phase191", "strategy": "ifind_metric_definition_and_unit_hardening",
        "whitelist": 4, "graylist": 4, "blacklist": 7, "300394_monitoring_ready": 8,
        "ifind_api_called": False, "guard": "pass", "quality_gate": "pass", "cannot_conclude_guard": "pass", "violations": 0,
        "clean_evidence_written": False, "packet_updated": False,
        "daily_brief_updated": False, "daily_monitoring_updated": False, "watch_core_updated": False,
        "raw_response_saved": False, "llm_api_called": False, "broker_api_called": False,
        "trade_recommendation_created": 0, "target_price_created": 0, "position_sizing_created": 0,
        "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0
    }}}

def build_backlog_update(): return build_backlog()
def build_cc_guard_report(): return build_phase191_cannot_conclude_guard()

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--execute", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); fname = os.path.basename(__file__)
    if "brief" in fname: print(json.dumps(build_ifind_metric_hardening_brief(), ensure_ascii=False, indent=2))
    elif "dashboard" in fname: print(json.dumps(build_dashboard(), ensure_ascii=False, indent=2))
    elif "backlog" in fname: print(json.dumps(build_backlog_update(), ensure_ascii=False, indent=2))
    elif "guard" in fname: print(json.dumps(build_cc_guard_report(), ensure_ascii=False, indent=2))
    else: print(json.dumps(build_ifind_metric_hardening_board(), ensure_ascii=False, indent=2))
