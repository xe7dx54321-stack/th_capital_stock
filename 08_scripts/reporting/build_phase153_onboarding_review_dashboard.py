import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase153_config import load_phase153_config
    from build_phase153_onboarding_review_board import build as build_board
    from smr_phase153_quality_gate import run_phase153_quality_gate
    from smr_phase153_guard import run_phase153_onboarding_guard
    from smr_phase153_cannot_conclude_guard import run_phase153_cannot_conclude_guard
    from smr_phase153_backlog import build_phase153_backlog

    board = build_board()["phase153_onboarding_review_board"]
    gate = run_phase153_quality_gate()
    guard = run_phase153_onboarding_guard()
    cc_guard = run_phase153_cannot_conclude_guard(board["packets"])
    backlog = build_phase153_backlog(board["packets"])

    return {"phase153_onboarding_review_dashboard": {
        "config": load_phase153_config(),
        "board": board,
        "quality_gate": gate["phase153_quality_gate"],
        "guard": guard["phase153_onboarding_guard"],
        "cannot_conclude_guard": cc_guard["phase153_cannot_conclude_guard"],
        "backlog": backlog["phase153_backlog"],
        "research_only": True,
        "activation_allowed": False, "auto_add_to_watchlist_allowed": False,
        "auto_promote_to_core_allowed": False,
        "judge_pass_not_investment_approval": True,
        "onboarding_review_not_watch_activation": True,
        "watch_core_updated": False, "candidate_auto_activated": False,
        "mock_used": False, "fixture_used": False,
        "trade_recommendation_created": 0, "target_price_created": 0,
        "position_sizing_created": 0, "paper_order_created": 0, "paper_trade_created": 0,
        "broker_api_called": False, "llm_api_called": False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
