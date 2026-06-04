# Phase175 console integration
import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase175_task_executor import run_all_tasks

def build_console_integration(mode="execute"):
    r = run_all_tasks(mode)
    ex = r["phase175_task_executor"]
    return {"phase175_console_integration":{"phase175_integrated":True,"task_executor_connected":True,"completed":ex["completed"],"failed":ex["failed"],"deferred":ex["deferred"],"research_only":True,"mock_used":False,"fixture_used":False}}

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--mode",default="execute")
    args = p.parse_args()
    print(json.dumps(build_console_integration(args.mode),ensure_ascii=False,indent=2))
