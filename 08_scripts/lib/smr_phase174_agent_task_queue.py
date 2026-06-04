# Phase174 agent task queue
from smr_phase174_coverage_state_registry import build_coverage_state_registry

def build_agent_task_queue():
    registry = build_coverage_state_registry()
    r = registry["phase174_coverage_state_registry"]
    tasks = []
    for e in r["entries"]:
        if not e["agent_task_eligible"]:
            continue
        tier = e["coverage_tier"]
        cid = e["candidate_id"]
        task_list = []
        if tier == "formal_research_coverage":
            task_list = [
                {"task_type":"daily_signal_monitoring","status":"pending_scheduled","agent":"quant_monitor"},
                {"task_type":"weekly_thesis_review","status":"pending_scheduled","agent":"research_analyst"},
                {"task_type":"evidence_refresh","status":"pending_scheduled","agent":"evidence_collector"},
                {"task_type":"coverage_drift_alert","status":"pending_scheduled","agent":"drift_monitor"}
            ]
        elif tier == "candidate_pending":
            task_list = [
                {"task_type":"evidence_gap_fill","status":"pending_owner_input","agent":"evidence_collector"},
                {"task_type":"milestone_check","status":"pending_scheduled","agent":"research_analyst"}
            ]
        elif tier == "deferred_review":
            task_list = [
                {"task_type":"binary_event_watch","status":"pending_scheduled","agent":"event_monitor"}
            ]
        tasks.append({
            "candidate_id":cid,"coverage_tier":tier,"tasks":task_list,"task_count":len(task_list)
        })
    return {"phase174_agent_task_queue":{
        "agent_task_queue_enabled":True,
        "candidates_with_tasks":len(tasks),
        "total_tasks":sum(t["task_count"] for t in tasks),
        "tasks":tasks,
        "no_trade_tasks":True,
        "no_order_tasks":True,
        "no_target_price_tasks":True,
        "cannot_conclude":["agent_tasks_are_research_only","tasks_do_not_execute_trades"],
        "mock_used":False,"fixture_used":False
    }}
