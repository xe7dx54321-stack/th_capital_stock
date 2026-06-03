import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))
from smr_phase148_config import load_phase148_config
from smr_phase148_candidate_profiles import build_candidate_profiles
from smr_phase148_activation_plan_builder import build_activation_plans
from smr_phase148_quality_gate import run_phase148_quality_gate
from smr_phase148_guard import run_phase148_guard
from smr_phase148_backlog import build_phase148_backlog

def build():
    return {"phase148_candidate_dashboard": {
        "config": load_phase148_config(),
        "profiles": build_candidate_profiles()["phase148_candidate_profiles"],
        "activation_plans": build_activation_plans()["phase148_activation_plans"],
        "quality_gate": run_phase148_quality_gate()["phase148_quality_gate"],
        "guard": run_phase148_guard()["phase148_cannot_conclude_guard"],
        "backlog": build_phase148_backlog()["phase148_backlog"],
        "research_only": True, "auto_add_to_watchlist": False, "mock_used": False, "fixture_used": False,
        "trade_recommendation_created": 0, "paper_order_created": 0,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
