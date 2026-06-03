import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))
from smr_phase150_config import load_phase150_config
from smr_phase150_tier_assignment import build_tier_assignments
from smr_phase150_capacity_model import build_capacity_model
from smr_phase150_quality_gate import run_phase150_quality_gate
from smr_phase150_guard import run_phase150_guard
from smr_phase150_backlog import build_phase150_backlog

def build():
    return {"phase150_tiering_dashboard": {
        "config": load_phase150_config(),
        "tier_assignments": build_tier_assignments()["phase150_tier_assignments"],
        "capacity_model": build_capacity_model()["phase150_capacity_model"],
        "quality_gate": run_phase150_quality_gate()["phase150_quality_gate"],
        "guard": run_phase150_guard()["phase150_cannot_conclude_guard"],
        "backlog": build_phase150_backlog()["phase150_backlog"],
        "research_only": True, "mock_used": False, "fixture_used": False,
        "trade_recommendation_created": 0, "paper_order_created": 0,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
