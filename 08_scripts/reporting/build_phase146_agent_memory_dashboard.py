import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))
from smr_phase146_config import load_phase146_config
from smr_phase146_agent_memory import build_agent_memory
from smr_phase146_task_queue import build_task_queue
from smr_phase146_handoff_builder import build_handoff_records
from smr_phase146_delivery_integration import build_delivery_integration
from smr_phase146_quality_gate import run_phase146_quality_gate
from smr_phase146_guard import run_phase146_guard
from smr_phase146_backlog import build_phase146_backlog

def build():
    return {"phase146_agent_memory_dashboard": {
        "config": load_phase146_config(),
        "agent_memory": build_agent_memory()["phase146_agent_memory"],
        "task_queue": build_task_queue()["phase146_task_queue"],
        "handoff_records": build_handoff_records()["phase146_handoff_records"],
        "delivery_integration": build_delivery_integration()["phase146_delivery_integration"],
        "quality_gate": run_phase146_quality_gate()["phase146_quality_gate"],
        "guard": run_phase146_guard()["phase146_cannot_conclude_guard"],
        "backlog": build_phase146_backlog()["phase146_backlog"],
        "research_only": True, "mock_used": False, "fixture_used": False,
        "trade_recommendation_created": 0, "paper_order_created": 0,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
