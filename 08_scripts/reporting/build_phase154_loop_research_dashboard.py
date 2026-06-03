import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase154_config import load_phase154_config
    from build_phase154_loop_research_board import build as build_board
    from smr_phase154_quality_gate import run_phase154_quality_gate
    from smr_phase154_guard import run_phase154_loop_guard
    from smr_phase154_cannot_conclude_guard import run_phase154_cannot_conclude_guard
    from smr_phase154_backlog import build_phase154_backlog

    board = build_board()["phase154_loop_research_board"]
    gate = run_phase154_quality_gate()
    guard = run_phase154_loop_guard()
    agents_list = [board["agents"][k] for k in ["opportunity","evidence","risk","thesis","deep_dive","brief","feedback","judge"]]
    cc_guard = run_phase154_cannot_conclude_guard(agents_list)
    backlog = build_phase154_backlog(board["loop_input"]["all_targets"])

    return {"phase154_loop_research_dashboard": {
        "config": load_phase154_config(), "board": board,
        "quality_gate": gate["phase154_quality_gate"], "guard": guard["phase154_loop_guard"],
        "cannot_conclude_guard": cc_guard["phase154_cannot_conclude_guard"],
        "backlog": backlog["phase154_backlog"],
        "research_only": True, "agent_simulation_only": True, "live_llm_call_made": False,
        "watch_core_updated": False, "candidate_auto_activated": False,
        "mock_used": False, "fixture_used": False,
        "trade_recommendation_created": 0, "target_price_created": 0,
        "position_sizing_created": 0, "paper_order_created": 0, "paper_trade_created": 0,
        "broker_api_called": False, "llm_api_called": False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
