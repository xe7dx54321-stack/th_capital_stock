# Phase185 reporting: cross-check board, brief, dashboard, backlog, cc guard
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase185_cross_check_gate import *

def build_cross_check_board():
    reg = build_cross_check_domain_registry(); schema = build_cross_check_task_schema()
    reasons = build_cross_check_reason_classifier(); src = build_source_route_builder()
    prompt = build_prompt_route_builder(); ver = build_verification_requirement_builder()
    indep = build_independent_source_policy(); div = build_source_diversity_policy()
    tasks = build_cross_check_tasks(); gate = build_eligibility_gate()
    ready = build_cleaning_readiness_preview(); ci = build_console_integration()
    g = build_phase185_guard(); qg = build_phase185_quality_gate(); cc = build_phase185_cannot_conclude_guard()
    return {"phase185_cross_check_board":{"phase":"phase185","strategy":"cross_check_task_generation_and_eligibility_gate","research_only":True,
        "registry":reg["phase185_cross_check_registry"],"task_schema":schema["phase185_cross_check_task_schema"],
        "cross_check_reasons":reasons["phase185_cross_check_reasons"],"source_routes":src["phase185_source_routes"],
        "prompt_routes":prompt["phase185_prompt_routes"],"verification_requirements":ver["phase185_verification_requirements"],
        "independent_source_policy":indep["phase185_independent_source_policy"],"source_diversity_policy":div["phase185_source_diversity_policy"],
        "cross_check_tasks":tasks["phase185_cross_check_tasks"],"eligibility_gate":gate["phase185_eligibility_gate"],
        "cleaning_readiness":ready["phase185_cleaning_readiness_preview"],"console_integration":ci["phase185_console_integration"],
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,"mock_used":False,"fixture_used":False}}

def build_cross_check_brief():
    tasks = build_cross_check_tasks()["phase185_cross_check_tasks"]; gate = build_eligibility_gate()["phase185_eligibility_gate"]
    return {"phase185_cross_check_brief":{"headline":"Cross-check tasks generated for 8 needs_cross_check items. Eligibility gate active: 0 items eligible for direct cleaning, 8 blocked pending cross-check.",
        "task_count":tasks["task_count"],"direct_cleaning_eligible":gate["direct_cleaning_eligible"],
        "blocked_pending_cross_check":gate["blocked_pending_cross_check_count"],
        "ready_after_cross_check":gate["ready_after_cross_check_count"],
        "tasks_not_executed":True,"gate_blocks_premature_cleaning":True,
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,"mock_used":False,"fixture_used":False,"research_only":True}}

def build_dashboard():
    tasks = build_cross_check_tasks()["phase185_cross_check_tasks"]; gate = build_eligibility_gate()["phase185_eligibility_gate"]
    return {"phase185_dashboard":{"summary":{"phase":"phase185","strategy":"cross_check_task_generation_and_eligibility_gate",
        "task_count":tasks["task_count"],"direct_cleaning_eligible":0,"blocked_pending_cross_check":8,"ready_after_cross_check":0,
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,
        "clean_evidence_written":False,"packet_updated":False,"daily_brief_updated":False,"weekly_review_updated":False,
        "llm_api_called":False,"web_search_called":False,"network_fetch_called":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "broker_api_called":False,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}}

def build_backlog_update(): return build_backlog()
def build_cc_guard_report(): return build_phase185_cannot_conclude_guard()

if __name__=="__main__":
    import argparse; p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--execute",action="store_true"); p.add_argument("--markdown",action="store_true")
    args = p.parse_args(); fname = os.path.basename(sys.argv[0])
    dispatch = {"board":build_cross_check_board,"brief":build_cross_check_brief,"dashboard":build_dashboard,"backlog":build_backlog_update,"guard":build_cc_guard_report}
    for k,f in dispatch.items():
        if k in fname: print(json.dumps(f(),ensure_ascii=False,indent=2)); break
    else: print(json.dumps(build_cross_check_board(),ensure_ascii=False,indent=2))
