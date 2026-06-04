# Phase174 post-apply console
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase174_coverage_state_registry import build_coverage_state_registry
from smr_phase174_coverage_state_loader import load_coverage_state
from smr_phase174_coverage_cards import build_coverage_cards
from smr_phase174_daily_monitoring_plan import build_daily_monitoring_plan
from smr_phase174_weekly_review_plan import build_weekly_review_plan
from smr_phase174_agent_task_queue import build_agent_task_queue
from smr_phase174_coverage_state_history import build_coverage_state_history
from smr_phase174_manual_adjustment import build_manual_adjustment_workflow
from smr_phase174_coverage_drift_checker import build_coverage_drift_checker
from smr_phase174_trade_term_debt import build_trade_term_debt_recorder
from smr_phase174_guard import build_phase174_guard, build_phase174_quality_gate, build_phase174_cannot_conclude_guard

def build_post_apply_console():
    state = load_coverage_state()
    cards = build_coverage_cards()
    daily = build_daily_monitoring_plan()
    weekly = build_weekly_review_plan()
    tasks = build_agent_task_queue()
    history = build_coverage_state_history()
    adjustment = build_manual_adjustment_workflow()
    drift = build_coverage_drift_checker()
    debt = build_trade_term_debt_recorder()
    guard = build_phase174_guard()
    qg = build_phase174_quality_gate()
    cc = build_phase174_cannot_conclude_guard()

    result = {
        "phase174_post_apply_console":{
            "phase":"phase174",
            "strategy":"post_apply_formal_research_coverage_console_and_monitoring_loop",
            "research_only":True,
            "coverage_state_loaded":state["phase174_coverage_state_loader"]["state_loaded"],
            "coverage_state_count":state["phase174_coverage_state_loader"]["coverage_state_count"],
            "activated_count":state["phase174_coverage_state_loader"]["activated_count"],
            "kept_count":state["phase174_coverage_state_loader"]["kept_count"],
            "deferred_count":state["phase174_coverage_state_loader"]["deferred_count"],
            "rejected_count":state["phase174_coverage_state_loader"]["rejected_count"],
            "coverage_cards_generated":cards["phase174_coverage_cards"]["cards_count"],
            "daily_monitoring_eligible":daily["phase174_daily_monitoring_plan"]["eligible_candidates"],
            "weekly_review_eligible":weekly["phase174_weekly_review_plan"]["eligible_candidates"],
            "agent_tasks_generated":tasks["phase174_agent_task_queue"]["total_tasks"],
            "agent_tasks_no_trade":tasks["phase174_agent_task_queue"]["no_trade_tasks"],
            "state_history_runs":history["phase174_coverage_state_history"]["runs_recorded"],
            "state_history_path_ignored":history["phase174_coverage_state_history"]["history_path_ignored"],
            "manual_adjustment_enabled":adjustment["phase174_manual_adjustment_workflow"]["manual_adjustment_enabled"],
            "drift_check_pass":drift["phase174_coverage_drift_checker"]["drift_detected"]==0,
            "trade_term_debt_recorded":debt["phase174_trade_term_debt"]["debt_recorded"],
            "guard":guard["phase174_guard"]["status"],
            "quality_gate":qg["phase174_quality_gate"]["status"],
            "cannot_conclude_guard":cc["phase174_cannot_conclude_guard"]["status"],
            "violations":qg["phase174_quality_gate"]["violations"],
            "watch_core_updated":False,
            "candidate_auto_activated":False,
            "trade_recommendation_created":0,
            "target_price_created":0,
            "position_sizing_created":0,
            "broker_api_called":False,
            "llm_api_called":False,
            "mock_used":False,"fixture_used":False,
            "pending_created":0,"paper_order_created":0,"real_trade_created":0,
            "next_phase_recommendation":"Phase175: Integrate post-apply coverage into daily research production loop with live agent execution."
        }
    }
    return result

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--json",action="store_true")
    p.add_argument("--execute",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args = p.parse_args()
    result = build_post_apply_console()
    print(json.dumps(result,ensure_ascii=False,indent=2))
