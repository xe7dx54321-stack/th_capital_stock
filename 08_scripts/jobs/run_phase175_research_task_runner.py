# Phase175 research task runner pipeline
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase175_task_queue_loader import load_task_queue
from smr_phase175_task_executor import run_all_tasks, write_task_artifacts, write_task_history
from smr_phase175_guard import (build_phase175_guard, build_phase175_quality_gate,
    build_phase175_cannot_conclude_guard, build_retry_planner, build_degraded_handler)
from datetime import datetime

def run_pipeline(mode="dry-run"):
    execute = mode == "execute"
    q = load_task_queue()
    r = run_all_tasks(mode)
    ex = r["phase175_task_executor"]
    artifacts_result = write_task_artifacts(r, mode) if execute else {"artifacts_written":False,"reason":"not_execute_mode"}
    history_result = write_task_history(r, mode) if execute else {"history_written":False,"reason":"not_execute_mode"}
    retry = build_retry_planner(mode)
    degraded = build_degraded_handler(mode)
    guard = build_phase175_guard()
    qg = build_phase175_quality_gate()
    cc = build_phase175_cannot_conclude_guard()

    return {"phase175_research_task_runner_pipeline":{
        "mode":mode,"phase":"phase175",
        "strategy":"agent_task_queue_live_execution_gate_and_research_task_runner",
        "research_only":True,"run_id":f"phase175-{datetime.now().strftime('%Y-%m-%d')}",
        "task_queue_loaded":True,
        "task_count":q["phase175_task_queue_loader"]["task_count"],
        "candidate_count":q["phase175_task_queue_loader"]["candidate_count"],
        "agent_count":q["phase175_task_queue_loader"]["agent_count"],
        "completed":ex["completed"],"failed":ex["failed"],"deferred":ex["deferred"],
        "artifacts_written":artifacts_result.get("artifacts_written",False),
        "artifacts_path_ignored":artifacts_result.get("path_ignored",True),
        "history_written":history_result.get("history_written",False),
        "history_path_ignored":history_result.get("path_ignored",True),
        "retry_count":retry["phase175_retry_planner"]["failed_count"],
        "degraded_count":degraded["phase175_degraded_handler"]["deferred_count"],
        "guard":guard["phase175_guard"]["status"],
        "quality_gate":qg["phase175_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase175_cannot_conclude_guard"]["status"],
        "violations":qg["phase175_quality_gate"]["violations"],
        "llm_api_called":False,"broker_api_called":False,
        "target_price_created":0,"position_sizing_created":0,
        "watch_core_updated":False,"candidate_auto_activated":False,
        "mock_used":False,"fixture_used":False,
        "raw_saved":False,"ocr_used":False,"browser_automation_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase176: Coverage state audit and reconciliation."
    }}

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true"); p.add_argument("--json",action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else ("skip-network" if getattr(args,"skip_network",False) else "dry-run")
    result = run_pipeline(mode)
    print(json.dumps(result,ensure_ascii=False,indent=2))
