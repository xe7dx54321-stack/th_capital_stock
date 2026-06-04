# Phase175 task queue loader - loads from Phase174 agent task queue
import sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase174_agent_task_queue import build_agent_task_queue

AGENT_TYPES = ["quant_monitor","research_analyst","evidence_collector","drift_monitor","event_monitor","thesis_validator","source_auditor"]

def load_task_queue():
    raw = build_agent_task_queue()
    tasks_raw = raw["phase174_agent_task_queue"]
    all_tasks = []
    for entry in tasks_raw["tasks"]:
        cid = entry["candidate_id"]
        tier = entry["coverage_tier"]
        for t in entry["tasks"]:
            all_tasks.append({
                "task_id":f"{cid}_{t['task_type']}",
                "candidate_id":cid,
                "coverage_tier":tier,
                "task_type":t["task_type"],
                "agent":t["agent"],
                "status":"pending",
                "priority":"normal",
                "dependencies":[],
                "retry_count":0,
                "max_retries":2
            })
    return {"phase175_task_queue_loader":{
        "task_queue_loaded":True,
        "task_count":len(all_tasks),
        "candidate_count":len(set(t["candidate_id"] for t in all_tasks)),
        "agent_count":len(AGENT_TYPES),
        "tasks":all_tasks,
        "source":"phase174_agent_task_queue",
        "mock_used":False,"fixture_used":False
    }}
