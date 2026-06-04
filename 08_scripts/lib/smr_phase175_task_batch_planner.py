# Phase175 task schema, eligibility checker, batch planner
from smr_phase175_task_queue_loader import load_task_queue, AGENT_TYPES

AGENT_TASK_MAP = {
    "quant_monitor":["daily_signal_monitoring"],
    "research_analyst":["weekly_thesis_review","milestone_check","thesis_seed_review","brief_card_prepare","next_review_marker"],
    "evidence_collector":["evidence_refresh","evidence_gap_fill","evidence_gap_followup","evidence_waitlist_followup","source_availability_check"],
    "drift_monitor":["coverage_drift_alert"],
    "event_monitor":["binary_event_watch"],
    "thesis_validator":["judge_recheck","formal_research_packet_prepare","archive_decision_record"],
    "source_auditor":["source_limitation_review"]
}

def build_task_schema():
    return {"phase175_task_schema":{
        "task_fields":["task_id","candidate_id","coverage_tier","task_type","agent","status","priority","dependencies","retry_count","max_retries"],
        "statuses":["pending","eligible","running","completed","failed","deferred","skipped"],
        "agent_types":AGENT_TYPES,
        "agent_task_map":AGENT_TASK_MAP,
        "mock_used":False,"fixture_used":False
    }}

def check_task_eligibility(mode="execute"):
    q = load_task_queue()
    tasks = q["phase175_task_queue_loader"]["tasks"]
    eligible = []; deferred = []
    for t in tasks:
        is_network = t["task_type"] in ["source_availability_check","evidence_gap_followup","evidence_waitlist_followup"]
        if mode == "skip-network" and is_network:
            t["status"] = "deferred"; deferred.append(t)
        elif mode == "dry-run":
            t["status"] = "eligible"; eligible.append(t)
        else:
            t["status"] = "eligible"; eligible.append(t)
    return {"phase175_task_eligibility":{
        "mode":mode,"total_tasks":len(tasks),
        "eligible_count":len(eligible),"deferred_count":len(deferred),
        "eligible":eligible,"deferred":deferred,
        "mock_used":False,"fixture_used":False
    }}

def build_batch_plan(mode="execute"):
    eligibility = check_task_eligibility(mode)
    eligible = eligibility["phase175_task_eligibility"]["eligible"]
    batches = []
    batch_size = 5
    for i in range(0,len(eligible),batch_size):
        batch = eligible[i:i+batch_size]
        batches.append({"batch_id":len(batches)+1,"task_count":len(batch),"tasks":batch})
    return {"phase175_task_batch_planner":{
        "mode":mode,"eligible_tasks":len(eligible),
        "batch_count":len(batches),"max_concurrent":batch_size,
        "batches":batches,
        "mock_used":False,"fixture_used":False
    }}
