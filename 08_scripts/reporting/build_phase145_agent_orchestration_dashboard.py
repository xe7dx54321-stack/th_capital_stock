import json, sys, os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

from smr_phase145_config import load_phase145_config
from smr_phase145_agent_registry import build_agent_registry
from smr_phase145_task_schema import build_task_schema
from smr_phase145_orchestrator import build_orchestrator_state
from smr_phase145_dependency_graph import build_dependency_graph
from smr_phase145_quality_gate import run_phase145_quality_gate
from smr_phase145_guard import run_phase145_guard
from smr_phase145_backlog import build_phase145_backlog


def build():
    cfg = load_phase145_config()
    registry = build_agent_registry()
    schema = build_task_schema()
    orch = build_orchestrator_state()
    graph = build_dependency_graph()
    quality = run_phase145_quality_gate()
    guard = run_phase145_guard()
    backlog = build_phase145_backlog()

    return {
        "phase145_agent_orchestration_dashboard": {
            "config": cfg,
            "agent_registry": registry["phase145_agent_registry"],
            "task_schema": schema["phase145_task_schema"],
            "orchestrator": orch["phase145_orchestrator"],
            "dependency_graph": graph["phase145_dependency_graph"],
            "quality_gate": quality["phase145_quality_gate"],
            "guard": guard["phase145_cannot_conclude_guard"],
            "backlog": backlog["phase145_backlog"],
            "research_only": True,
            "auto_dispatch_allowed": False,
            "mock_used": False, "fixture_used": False,
            "trade_recommendation_created": 0,
            "target_price_created": 0,
            "paper_order_created": 0,
        }
    }


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
