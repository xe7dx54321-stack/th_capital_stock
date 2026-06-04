# Phase175 dashboard
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase175_task_queue_loader import load_task_queue
from smr_phase175_task_executor import run_all_tasks
from smr_phase175_guard import build_phase175_guard, build_phase175_quality_gate, build_phase175_cannot_conclude_guard

def build_dashboard(mode="execute"):
    q = load_task_queue()
    r = run_all_tasks(mode)
    ex = r["phase175_task_executor"]
    guard = build_phase175_guard()
    qg = build_phase175_quality_gate()
    cc = build_phase175_cannot_conclude_guard()
    return {"phase175_dashboard":{"summary":{"phase":"phase175","strategy":"agent_task_queue_live_execution_gate","task_count":q["phase175_task_queue_loader"]["task_count"],"candidate_count":q["phase175_task_queue_loader"]["candidate_count"],"agent_count":q["phase175_task_queue_loader"]["agent_count"],"completed":ex["completed"],"failed":ex["failed"],"deferred":ex["deferred"],"guard":guard["phase175_guard"]["status"],"quality_gate":qg["phase175_quality_gate"]["status"],"cannot_conclude_guard":cc["phase175_cannot_conclude_guard"]["status"],"violations":qg["phase175_quality_gate"]["violations"],"llm_api_called":False,"broker_api_called":False,"target_price_created":0,"position_sizing_created":0,"watch_core_updated":False,"mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}}

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--mode",default="execute")
    args = p.parse_args()
    print(json.dumps(build_dashboard(args.mode),ensure_ascii=False,indent=2))
