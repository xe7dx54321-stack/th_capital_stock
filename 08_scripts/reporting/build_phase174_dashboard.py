# Phase174 dashboard
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase174_coverage_state_loader import load_coverage_state
from smr_phase174_coverage_cards import build_coverage_cards
from smr_phase174_daily_monitoring_plan import build_daily_monitoring_plan
from smr_phase174_weekly_review_plan import build_weekly_review_plan
from smr_phase174_agent_task_queue import build_agent_task_queue
from smr_phase174_guard import build_phase174_guard, build_phase174_quality_gate, build_phase174_cannot_conclude_guard

def build_dashboard():
    state = load_coverage_state()
    cards = build_coverage_cards()
    daily = build_daily_monitoring_plan()
    weekly = build_weekly_review_plan()
    tasks = build_agent_task_queue()
    guard = build_phase174_guard()
    qg = build_phase174_quality_gate()
    cc = build_phase174_cannot_conclude_guard()

    sl = state["phase174_coverage_state_loader"]
    return {"phase174_dashboard":{
        "summary":{
            "phase":"phase174","strategy":"post_apply_formal_research_coverage_console",
            "coverage_state_count":sl["coverage_state_count"],
            "activated_count":sl["activated_count"],
            "kept_count":sl["kept_count"],
            "deferred_count":sl["deferred_count"],
            "rejected_count":sl["rejected_count"],
            "coverage_cards":cards["phase174_coverage_cards"]["cards_count"],
            "daily_monitoring_eligible":daily["phase174_daily_monitoring_plan"]["eligible_candidates"],
            "weekly_review_eligible":weekly["phase174_weekly_review_plan"]["eligible_candidates"],
            "agent_tasks":tasks["phase174_agent_task_queue"]["total_tasks"],
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
            "pending_created":0,"paper_order_created":0,"real_trade_created":0
        }
    }}

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--json",action="store_true")
    args = p.parse_args()
    print(json.dumps(build_dashboard(),ensure_ascii=False,indent=2))
