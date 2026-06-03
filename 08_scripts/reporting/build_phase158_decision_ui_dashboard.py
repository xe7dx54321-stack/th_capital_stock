import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase158_config import load_phase158_config
    from build_phase158_decision_ui_board import build as build_board
    from smr_phase158_quality_gate import run_phase158_quality_gate
    from smr_phase158_guard import run_phase158_ui_guard
    from smr_phase158_cannot_conclude_guard import run_phase158_cannot_conclude_guard
    from smr_phase158_backlog import build_phase158_backlog
    from smr_phase158_loaders import load_pending_candidates

    board = build_board()["phase158_decision_ui_board"]
    gate = run_phase158_quality_gate()
    guard = run_phase158_ui_guard()
    cc = run_phase158_cannot_conclude_guard()
    candidates = load_pending_candidates()
    backlog = build_phase158_backlog(candidates)

    return {"phase158_decision_ui_dashboard":{
        "config":load_phase158_config(),"board":board,
        "quality_gate":gate["phase158_quality_gate"],"guard":guard["phase158_ui_guard"],
        "cannot_conclude_guard":cc["phase158_cannot_conclude_guard"],
        "backlog":backlog["phase158_backlog"],
        "research_only":True,"static_html_only":True,
        "watch_core_updated":False,"candidate_auto_activated":False,
        "mock_used":False,"fixture_used":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "paper_order_created":0,"paper_trade_created":0,"broker_api_called":False,"llm_api_called":False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
