import json, sys, os, argparse
from pathlib import Path
from datetime import datetime
BASE_LIB = Path(__file__).resolve().parent.parent / "lib"
BASE_REPORTING = Path(__file__).resolve().parent.parent / "reporting"
sys.path.insert(0, str(BASE_LIB)); sys.path.insert(0, str(BASE_REPORTING))
from build_phase146_agent_memory_dashboard import build

def run_pipeline(mode="dry-run"):
    started_at = datetime.now().isoformat()
    result = build(); dash = result["phase146_agent_memory_dashboard"]
    return {"phase146_agent_memory_pipeline": {
        "mode": mode, "started_at": started_at, "finished_at": datetime.now().isoformat(),
        "agents_with_memory": dash["agent_memory"]["agents"],
        "tasks_queued": dash["task_queue"]["summary"]["total"],
        "tasks_blocked": dash["task_queue"]["summary"]["blocked"],
        "handoffs_recorded": dash["handoff_records"]["handoffs"],
        "delivery_linked": dash["delivery_integration"]["daily_items"] > 0,
        "quality_gate": dash["quality_gate"]["overall_status"],
        "guard": dash["guard"]["overall_status"], "violations": dash["guard"]["violations"],
        "research_only": True, "mock_used": False, "fixture_used": False,
        "trade_recommendation_created": 0, "paper_order_created": 0,
    }}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true"); p.add_argument("--skip-network", action="store_true"); p.add_argument("--json", action="store_true")
    a = p.parse_args()
    mode = "execute" if a.execute else ("skip-network" if a.skip_network else "dry-run")
    print(json.dumps(run_pipeline(mode), indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__": main()
