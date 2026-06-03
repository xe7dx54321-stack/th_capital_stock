import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase157_config import load_phase157_config
    from build_phase157_decision_board import build as build_board
    from smr_phase157_quality_gate import run_phase157_quality_gate
    from smr_phase157_guard import run_phase157_decision_guard
    from smr_phase157_cannot_conclude_guard import run_phase157_cannot_conclude_guard
    from smr_phase157_backlog import build_phase157_backlog
    from smr_phase157_loaders import load_ready_candidates

    board = build_board()["phase157_decision_board"]
    gate = run_phase157_quality_gate()
    guard = run_phase157_decision_guard()
    cc = run_phase157_cannot_conclude_guard()
    candidates = load_ready_candidates()
    backlog = build_phase157_backlog(candidates)

    return {"phase157_decision_dashboard":{
        "config":load_phase157_config(),"board":board,
        "quality_gate":gate["phase157_quality_gate"],"guard":guard["phase157_decision_guard"],
        "cannot_conclude_guard":cc["phase157_cannot_conclude_guard"],
        "backlog":backlog["phase157_backlog"],
        "research_only":True,"simulation_only":True,"execution_blocked":True,
        "watch_core_updated":False,"candidate_auto_activated":False,
        "mock_used":False,"fixture_used":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "paper_order_created":0,"paper_trade_created":0,"broker_api_called":False,"llm_api_called":False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
