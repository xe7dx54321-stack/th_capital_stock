# Phase185 runner
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase185_cross_check_gate import *

def run_pipeline(mode="dry-run"):
    reg = build_cross_check_domain_registry()
    tasks = build_cross_check_tasks()
    gate = build_eligibility_gate()
    ready = build_cleaning_readiness_preview()
    g = build_phase185_guard(); qg = build_phase185_quality_gate(); cc = build_phase185_cannot_conclude_guard()
    t = tasks["phase185_cross_check_tasks"]; gt = gate["phase185_eligibility_gate"]
    return {"phase185_cross_check_gate_pipeline":{"mode":mode,"phase":"phase185","strategy":"cross_check_task_generation_and_eligibility_gate","research_only":True,
        "input_dirty_items":8,"needs_cross_check_count":8,"candidate_evidence_count":0,
        "cross_check_task_count":t["task_count"],"source_route_count":8,"prompt_route_count":8,"verification_requirement_count":8,
        "direct_cleaning_eligible":gt["direct_cleaning_eligible"],"direct_cleaning_eligible_count":gt["direct_cleaning_eligible_count"],
        "blocked_pending_cross_check":gt["blocked_pending_cross_check"],"blocked_pending_cross_check_count":gt["blocked_pending_cross_check_count"],
        "ready_after_cross_check_count":gt["ready_after_cross_check_count"],
        "tasks_not_executed":True,"source_routes_not_network_fetch":True,"prompt_routes_not_llm_call":True,
        "eligibility_gate_active":True,"gate_not_clean_evidence_write":True,"gate_blocks_premature_cleaning":True,
        "cleaning_readiness_preview_generated":True,"cleaning_not_started":True,
        "guard":g["phase185_guard"]["status"],"quality_gate":qg["phase185_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase185_cannot_conclude_guard"]["status"],"violations":0,
        "llm_api_called":False,"web_search_called":False,"network_fetch_called":False,
        "clean_evidence_written":False,"packet_updated":False,"daily_brief_updated":False,"weekly_review_updated":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,"broker_api_called":False,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase186: Simulated Scout Execution and Cross-check Runner."}}

if __name__=="__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true"); p.add_argument("--json",action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args,"skip_network",False) else "dry-run")
    print(json.dumps(run_pipeline(mode),ensure_ascii=False,indent=2))
