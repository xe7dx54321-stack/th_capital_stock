import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))
from smr_phase149_config import load_phase149_config
from smr_phase149_agent_instructions import build_agent_instructions
from smr_phase149_quality_gate import run_phase149_quality_gate
from smr_phase149_guard import run_phase149_guard
from smr_phase149_backlog import build_phase149_backlog

def build():
    return {"phase149_agent_instructions_dashboard": {
        "config": load_phase149_config(),
        "instructions": build_agent_instructions()["phase149_agent_instructions"],
        "quality_gate": run_phase149_quality_gate()["phase149_quality_gate"],
        "guard": run_phase149_guard()["phase149_cannot_conclude_guard"],
        "backlog": build_phase149_backlog()["phase149_backlog"],
        "research_only": True, "mock_used": False, "fixture_used": False,
        "trade_recommendation_created": 0, "paper_order_created": 0,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
