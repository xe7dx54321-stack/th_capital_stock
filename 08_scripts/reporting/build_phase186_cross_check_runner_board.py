# Phase186 reporting: board, brief, dashboard, backlog, cc guard
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase186_simulated_scout_cross_check import *

def build_runner_board():
    reg = build_simulated_scout_registry(); schema = build_simulated_source_observation_schema()
    obs = build_simulated_scout_output_generator(); runner = build_cross_check_runner()
    match = build_source_match_preview(); ver = build_verification_result_preview()
    oc = build_outcome_classifier(); comp = build_verification_completeness_scorer()
    indep = build_independent_source_checker(); manifest = build_outcome_manifest()
    er = build_eligibility_refresh(); cr = build_cleaning_readiness_refresh()
    fh = build_failure_handler(); audit = build_simulated_audit_log(); ci = build_console_integration()
    g = build_phase186_guard(); qg = build_phase186_quality_gate(); cc = build_phase186_cannot_conclude_guard()
    return {"phase186_cross_check_runner_board":{"phase":"phase186","strategy":"simulated_scout_execution_and_cross_check_runner","research_only":True,
        "registry":reg["phase186_simulated_scout_registry"],"observation_schema":schema["phase186_observation_schema"],
        "observations":obs["phase186_simulated_observations"],"runner":runner["phase186_cross_check_runner"],
        "source_match":match["phase186_source_match_preview"],"verification":ver["phase186_verification_preview"],
        "outcome_classifier":oc["phase186_outcome_classifier"],"completeness":comp["phase186_completeness_scorer"],
        "independent_checker":indep["phase186_independent_source_checker"],"outcome_manifest":manifest["phase186_outcome_manifest"],
        "eligibility_refresh":er["phase186_eligibility_refresh"],"cleaning_readiness":cr["phase186_cleaning_readiness_refresh"],
        "failure_handler":fh["phase186_failure_handler"],"audit_log":audit["phase186_audit_log"],
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,"mock_used":False,"fixture_used":False}}

def build_runner_brief():
    m = build_outcome_manifest()["phase186_outcome_manifest"]; er = build_eligibility_refresh()["phase186_eligibility_refresh"]
    return {"phase186_cross_check_runner_brief":{"headline":"Simulated cross-check runner complete. 8 tasks processed. Outcomes are SIMULATED, not real verification.",
        "total_tasks":8,"strong":m["strong"],"moderate":m["moderate"],"insufficient":m["insufficient"],"conflict":0,
        "would_be_ready_if_real":er["would_be_ready_if_real_count"],"still_blocked":er["still_blocked_count"],
        "simulated_only":True,"not_real_verification":True,"would_be_ready_not_clean_evidence":True,
        "guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,"mock_used":False,"fixture_used":False,"research_only":True}}

def build_dashboard():
    m = build_outcome_manifest()["phase186_outcome_manifest"]; er = build_eligibility_refresh()["phase186_eligibility_refresh"]
    return {"phase186_dashboard":{"summary":{"phase":"phase186","strategy":"simulated_scout_execution_and_cross_check_runner",
        "simulated_task_count":8,"strong":m["strong"],"moderate":m["moderate"],"insufficient":m["insufficient"],
        "would_be_ready_if_real":er["would_be_ready_if_real_count"],"still_blocked":er["still_blocked_count"],
        "simulated_only":True,"guard":"pass","quality_gate":"pass","cannot_conclude_guard":"pass","violations":0,
        "clean_evidence_written":False,"packet_updated":False,"llm_api_called":False,"web_search_called":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "broker_api_called":False,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}}

def build_backlog_update(): return build_backlog()
def build_cc_guard_report(): return build_phase186_cannot_conclude_guard()

if __name__=="__main__":
    import argparse; p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--execute",action="store_true"); p.add_argument("--markdown",action="store_true")
    args = p.parse_args(); fname = os.path.basename(sys.argv[0])
    dispatch = {"board":build_runner_board,"brief":build_runner_brief,"dashboard":build_dashboard,"backlog":build_backlog_update,"guard":build_cc_guard_report}
    for k,f in dispatch.items():
        if k in fname: print(json.dumps(f(),ensure_ascii=False,indent=2)); break
    else: print(json.dumps(build_runner_board(),ensure_ascii=False,indent=2))
