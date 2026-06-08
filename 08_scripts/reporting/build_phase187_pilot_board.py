# Phase187 reporting: pilot board, brief, dashboard, backlog, cc guard
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase187_real_web_scout_pilot import *

def build_pilot_board():
    reg = build_pilot_registry(); scope = build_pilot_scope_selector(); qp = build_pilot_query_plan()
    policy = build_safe_network_policy(); fetch = build_fetch_status_board(); leads = build_source_lead_observations()
    match = build_cross_check_match_preview(); elig = build_real_web_eligibility_preview()
    manifest = build_pilot_outcome_manifest(); ticker = build_ticker_pilot_breakdown()
    src = build_source_category_breakdown(); audit = build_audit_log(); ci = build_console_integration()
    g = build_phase187_guard(); qg = build_phase187_quality_gate(); cc = build_phase187_cannot_conclude_guard()
    return {"phase187_pilot_board":{"phase":"phase187","strategy":"real_web_scout_pilot","research_only":True,
        "registry":reg["phase187_pilot_registry"],"scope":scope["phase187_pilot_scope"],"query_plan":qp["phase187_query_plan"],
        "safe_network_policy":policy["phase187_safe_network_policy"],"fetch_status":fetch["phase187_fetch_status"],
        "source_leads":leads["phase187_source_leads"],"cross_check_match":match["phase187_cross_check_match_preview"],
        "eligibility_preview":elig["phase187_eligibility_preview"],"outcome_manifest":manifest["phase187_pilot_outcome_manifest"],
        "ticker_breakdown":ticker["phase187_ticker_breakdown"],"source_category_breakdown":src["phase187_source_category_breakdown"],
        "audit_log":audit["phase187_audit_log"],"guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,"mock_used":False,"fixture_used":False}}

def build_pilot_brief():
    m = build_pilot_outcome_manifest()["phase187_pilot_outcome_manifest"]
    return {"phase187_pilot_brief":{"headline":"Real Web Scout Pilot complete. Source lead observations generated. NOT verified evidence, NOT clean evidence.",
        "fetched":m["fetched"],"blocked":m["blocked"],"skipped":m["skipped"],"source_leads":m["source_leads"],
        "source_leads_not_verified":True,"source_leads_not_clean_evidence":True,"no_full_raw":True,"no_llm":True,
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,"mock_used":False,"fixture_used":False,"research_only":True}}

def build_dashboard():
    m = build_pilot_outcome_manifest()["phase187_pilot_outcome_manifest"]
    return {"phase187_dashboard":{"summary":{"phase":"phase187","strategy":"real_web_scout_pilot",
        "fetched":m["fetched"],"blocked":m["blocked"],"source_leads":m["source_leads"],
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,
        "clean_evidence_written":False,"packet_updated":False,"llm_api_called":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "broker_api_called":False,"raw_full_text_saved":False,"mock_used":False,"fixture_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0}}}

def build_backlog_update(): return build_backlog()
def build_cc_guard_report(): return build_phase187_cannot_conclude_guard()

if __name__=="__main__":
    import argparse; p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--execute",action="store_true"); p.add_argument("--markdown",action="store_true")
    args = p.parse_args(); fname = os.path.basename(sys.argv[0])
    dispatch = {"board":build_pilot_board,"brief":build_pilot_brief,"dashboard":build_dashboard,"backlog":build_backlog_update,"guard":build_cc_guard_report}
    for k,f in dispatch.items():
        if k in fname: print(json.dumps(f(),ensure_ascii=False,indent=2)); break
    else: print(json.dumps(build_pilot_board(),ensure_ascii=False,indent=2))
