import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase159_config import load_phase159_config
    from build_phase159_submission_board import build as build_board
    from smr_phase159_quality_gate import run_phase159_quality_gate
    from smr_phase159_guard import run_phase159_submission_guard
    from smr_phase159_cannot_conclude_guard import run_phase159_cannot_conclude_guard
    from smr_phase159_backlog import build_phase159_backlog
    from smr_phase159_loaders import load_pending_candidates

    board = build_board()["phase159_submission_board"]
    gate = run_phase159_quality_gate()
    guard = run_phase159_submission_guard()
    cc = run_phase159_cannot_conclude_guard()
    candidates = load_pending_candidates()
    backlog = build_phase159_backlog(candidates)

    return {"phase159_submission_dashboard":{"config":load_phase159_config(),"board":board,
        "quality_gate":gate["phase159_quality_gate"],"guard":guard["phase159_submission_guard"],
        "cannot_conclude_guard":cc["phase159_cannot_conclude_guard"],"backlog":backlog["phase159_backlog"],
        "research_only":True,"submission_not_execution":True,"execution_blocked":True,
        "watch_core_updated":False,"candidate_auto_activated":False,
        "mock_used":False,"fixture_used":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "paper_order_created":0,"paper_trade_created":0,"broker_api_called":False,"llm_api_called":False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
