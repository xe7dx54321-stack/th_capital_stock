import json, sys, os, argparse
from pathlib import Path
from datetime import datetime

BASE_LIB = Path(__file__).resolve().parent.parent / "lib"
BASE_REPORTING = Path(__file__).resolve().parent.parent / "reporting"
sys.path.insert(0, str(BASE_LIB))
sys.path.insert(0, str(BASE_REPORTING))

from build_phase145_agent_orchestration_dashboard import build


def run_pipeline(mode="dry-run"):
    started_at = datetime.now().isoformat()
    result = build()
    dash = result["phase145_agent_orchestration_dashboard"]
    finished_at = datetime.now().isoformat()

    return {
        "phase145_agent_orchestration_pipeline": {
            "mode": mode,
            "started_at": started_at,
            "finished_at": finished_at,
            "agents_registered": dash["agent_registry"]["agents"],
            "tasks_total": dash["orchestrator"]["summary"]["total_tasks"],
            "tasks_completed": dash["orchestrator"]["summary"]["completed"],
            "tasks_pending": dash["orchestrator"]["summary"]["pending"],
            "quality_gate": dash["quality_gate"]["overall_status"],
            "guard": dash["guard"]["overall_status"],
            "violations": dash["guard"]["violations"],
            "research_only": True,
            "auto_dispatch_allowed": False,
            "mock_used": False, "fixture_used": False,
            "trade_recommendation_created": 0,
            "target_price_created": 0,
            "paper_order_created": 0,
        }
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--skip-network", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.execute:
        mode = "execute"
    elif args.skip_network:
        mode = "skip-network"
    else:
        mode = "dry-run"
    output = run_pipeline(mode)
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
