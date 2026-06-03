import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))
from smr_phase147_config import load_phase147_config
from smr_phase147_onboarding_pipeline import build_onboarding_pipeline
from smr_phase147_stage_checker import build_stage_checklist
from smr_phase147_quality_gate import run_phase147_quality_gate
from smr_phase147_guard import run_phase147_guard
from smr_phase147_backlog import build_phase147_backlog

def build():
    return {"phase147_onboarding_dashboard": {
        "config": load_phase147_config(),
        "pipeline": build_onboarding_pipeline()["phase147_onboarding_pipeline"],
        "stage_checklist": build_stage_checklist()["phase147_stage_checklist"],
        "quality_gate": run_phase147_quality_gate()["phase147_quality_gate"],
        "guard": run_phase147_guard()["phase147_cannot_conclude_guard"],
        "backlog": build_phase147_backlog()["phase147_backlog"],
        "research_only": True, "mock_used": False, "fixture_used": False,
        "trade_recommendation_created": 0, "paper_order_created": 0,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
