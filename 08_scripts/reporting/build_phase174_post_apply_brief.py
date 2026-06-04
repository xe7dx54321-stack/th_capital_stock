# Phase174 post-apply brief
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase174_coverage_state_registry import build_coverage_state_registry
from smr_phase174_coverage_state_loader import load_coverage_state
from smr_phase174_daily_monitoring_plan import build_daily_monitoring_plan
from smr_phase174_weekly_review_plan import build_weekly_review_plan
from smr_phase174_agent_task_queue import build_agent_task_queue
from smr_phase174_trade_term_debt import build_trade_term_debt_recorder
from smr_phase174_guard import build_phase174_guard, build_phase174_quality_gate, build_phase174_cannot_conclude_guard

def build_post_apply_brief():
    state = load_coverage_state()
    daily = build_daily_monitoring_plan()
    weekly = build_weekly_review_plan()
    tasks = build_agent_task_queue()
    debt = build_trade_term_debt_recorder()
    guard = build_phase174_guard()
    qg = build_phase174_quality_gate()
    cc = build_phase174_cannot_conclude_guard()

    sl = state["phase174_coverage_state_loader"]
    brief = {
        "phase174_post_apply_brief":{
            "phase":"phase174",
            "headline":"Post-apply formal research coverage console activated. 13 candidates in coverage state registry.",
            "sections":{
                "boss_summary":{
                    "total_candidates":sl["coverage_state_count"],
                    "formal_research_coverage":sl["activated_count"],
                    "candidate_pending":sl["kept_count"],
                    "deferred_review":sl["deferred_count"],
                    "rejected":sl["rejected_count"],
                    "key_message":"9 candidates now in formal research coverage with daily monitoring. 2 pending further evidence. 1 deferred for binary event. 1 rejected."
                },
                "monitoring_setup":{
                    "daily_monitoring_candidates":daily["phase174_daily_monitoring_plan"]["eligible_candidates"],
                    "weekly_review_candidates":weekly["phase174_weekly_review_plan"]["eligible_candidates"],
                    "agent_tasks_total":tasks["phase174_agent_task_queue"]["total_tasks"],
                    "monitoring_not_trade":True
                },
                "technical_debt":{
                    "trade_term_validator_debt":debt["phase174_trade_term_debt"]["known_issue"],
                    "severity":debt["phase174_trade_term_debt"]["debt_severity"],
                    "recommendation":debt["phase174_trade_term_debt"]["recommended_fix"]
                },
                "research_boundary":{
                    "coverage_state_only":True,
                    "no_watch_core_update":True,
                    "no_trade_recommendation":True,
                    "no_target_price":True,
                    "no_position_sizing":True,
                    "no_broker_api":True,
                    "no_llm_api":True
                }
            },
            "guard":guard["phase174_guard"]["status"],
            "quality_gate":qg["phase174_quality_gate"]["status"],
            "cannot_conclude_guard":cc["phase174_cannot_conclude_guard"]["status"],
            "violations":qg["phase174_quality_gate"]["violations"],
            "mock_used":False,"fixture_used":False,
            "pending_created":0,"paper_order_created":0,"real_trade_created":0
        }
    }
    return brief

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--json",action="store_true")
    p.add_argument("--execute",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args = p.parse_args()
    result = build_post_apply_brief()
    if args.markdown:
        b = result["phase174_post_apply_brief"]
        s = b["sections"]
        print("# Post-Apply Coverage Console Brief")
        print()
        print("## Boss Summary")
        print(f"- Total candidates: {s['boss_summary']['total_candidates']}")
        print(f"- Formal research coverage: {s['boss_summary']['formal_research_coverage']}")
        print(f"- Candidate pending: {s['boss_summary']['candidate_pending']}")
        print(f"- Deferred review: {s['boss_summary']['deferred_review']}")
        print(f"- Rejected: {s['boss_summary']['rejected']}")
        print()
        print(s['boss_summary']['key_message'])
        print()
        print("## Monitoring Setup")
        print(f"- Daily monitoring: {s['monitoring_setup']['daily_monitoring_candidates']} candidates")
        print(f"- Weekly review: {s['monitoring_setup']['weekly_review_candidates']} candidates")
        print(f"- Agent tasks: {s['monitoring_setup']['agent_tasks_total']} total")
        print()
        print("## Research Boundary")
        for k,v in s["research_boundary"].items():
            print(f"- {k}: {v}")
        print()
        print("## Guard Status")
        print(f"- guard: {b['guard']}")
        print(f"- quality_gate: {b['quality_gate']}")
        print(f"- cannot_conclude_guard: {b['cannot_conclude_guard']}")
    else:
        print(json.dumps(result,ensure_ascii=False,indent=2))
