# Phase175 reporting: task queue loader report, batch plan report, task execution report, agent execution report
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase175_task_queue_loader import load_task_queue
from smr_phase175_task_batch_planner import build_batch_plan, build_task_schema, check_task_eligibility, AGENT_TASK_MAP
from smr_phase175_task_executor import run_all_tasks, AGENT_EXECUTORS

def build_task_queue_loader_report():
    q = load_task_queue()
    return {"phase175_task_queue_loader_report":q["phase175_task_queue_loader"]}

def build_task_batch_plan_report(mode="execute"):
    bp = build_batch_plan(mode)
    return {"phase175_task_batch_plan_report":bp["phase175_task_batch_planner"]}

def build_task_execution_report(mode="execute"):
    r = run_all_tasks(mode)
    return {"phase175_task_execution_report":r["phase175_task_executor"]}

def build_agent_execution_report(mode="execute"):
    r = run_all_tasks(mode)
    results = r["phase175_task_executor"]["results"]
    agents = {}
    for r_ in results:
        ag = r_.get("agent","unknown")
        if ag not in agents: agents[ag] = {"completed":0,"failed":0,"deferred":0,"skipped":0}
        st = r_["status"]
        if st in agents[ag]: agents[ag][st] += 1
    return {"phase175_agent_execution_report":{"agent_count":len(AGENT_EXECUTORS),"agents":agents,"research_only":True,"mock_used":False,"fixture_used":False}}

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--json",action="store_true"); p.add_argument("--mode",default="execute")
    args = p.parse_args()
    mode = args.mode
    reports = {
        "task_queue_loader":build_task_queue_loader_report(),
        "task_batch_plan":build_task_batch_plan_report(mode),
        "task_execution":build_task_execution_report(mode),
        "agent_execution":build_agent_execution_report(mode)
    }
    print(json.dumps(reports,ensure_ascii=False,indent=2))
