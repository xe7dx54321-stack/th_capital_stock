import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))
from smr_phase151_config import load_phase151_config
from smr_phase151_discovery_sources import build_discovery_sources
from smr_phase151_discovery_queue import build_discovery_queue
from smr_phase151_quality_gate import run_phase151_quality_gate
from smr_phase151_guard import run_phase151_guard
from smr_phase151_backlog import build_phase151_backlog

def build():
    return {"phase151_discovery_dashboard": {
        "config": load_phase151_config(),
        "discovery_sources": build_discovery_sources()["phase151_discovery_sources"],
        "discovery_queue": build_discovery_queue()["phase151_discovery_queue"],
        "quality_gate": run_phase151_quality_gate()["phase151_quality_gate"],
        "guard": run_phase151_guard()["phase151_cannot_conclude_guard"],
        "backlog": build_phase151_backlog()["phase151_backlog"],
        "research_only": True, "mock_used": False, "fixture_used": False,
        "trade_recommendation_created": 0, "paper_order_created": 0,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
