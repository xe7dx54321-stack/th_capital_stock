import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase155_config import load_phase155_config
    from build_phase155_scheduling_board import build as build_board
    from smr_phase155_quality_gate import run_phase155_quality_gate
    from smr_phase155_guard import run_phase155_scheduling_guard
    from smr_phase155_cannot_conclude_guard import run_phase155_cannot_conclude_guard
    from smr_phase155_backlog import build_phase155_backlog
    from smr_phase155_loaders import load_phase154_loop_results

    board = build_board()["phase155_scheduling_board"]
    gate = run_phase155_quality_gate()
    guard = run_phase155_scheduling_guard()
    cc = run_phase155_cannot_conclude_guard()
    targets = load_phase154_loop_results()
    backlog = build_phase155_backlog(targets["all"])

    return {"phase155_scheduling_dashboard":{
        "config":load_phase155_config(),"board":board,
        "quality_gate":gate["phase155_quality_gate"],"guard":guard["phase155_scheduling_guard"],
        "cannot_conclude_guard":cc["phase155_cannot_conclude_guard"],
        "backlog":backlog["phase155_backlog"],
        "research_only":True,"agent_simulation_only":True,"live_llm_call_made":False,
        "watch_core_updated":False,"candidate_auto_activated":False,
        "mock_used":False,"fixture_used":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "paper_order_created":0,"paper_trade_created":0,"broker_api_called":False,"llm_api_called":False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
