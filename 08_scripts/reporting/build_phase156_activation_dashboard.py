import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase156_config import load_phase156_config
    from build_phase156_activation_board import build as build_board
    from smr_phase156_quality_gate import run_phase156_quality_gate
    from smr_phase156_guard import run_phase156_activation_guard
    from smr_phase156_cannot_conclude_guard import run_phase156_cannot_conclude_guard
    from smr_phase156_backlog import build_phase156_backlog
    from smr_phase156_loaders import load_ready_for_owner_candidates

    board = build_board()["phase156_activation_board"]
    gate = run_phase156_quality_gate()
    guard = run_phase156_activation_guard()
    cc = run_phase156_cannot_conclude_guard()
    candidates = load_ready_for_owner_candidates()
    backlog = build_phase156_backlog(candidates)

    return {"phase156_activation_dashboard":{
        "config":load_phase156_config(),"board":board,
        "quality_gate":gate["phase156_quality_gate"],"guard":guard["phase156_activation_guard"],
        "cannot_conclude_guard":cc["phase156_cannot_conclude_guard"],
        "backlog":backlog["phase156_backlog"],
        "research_only":True,"owner_decision_required":True,"auto_approval_allowed":False,
        "watch_core_updated":False,"candidate_auto_activated":False,
        "mock_used":False,"fixture_used":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "paper_order_created":0,"paper_trade_created":0,"broker_api_called":False,"llm_api_called":False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
