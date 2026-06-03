import json, sys, os, argparse
from pathlib import Path
from datetime import datetime
BASE_LIB = Path(__file__).resolve().parent.parent / "lib"
BASE_REPORTING = Path(__file__).resolve().parent.parent / "reporting"
sys.path.insert(0, str(BASE_LIB))
sys.path.insert(0, str(BASE_REPORTING))
from build_phase153_onboarding_review_dashboard import build

def run(mode="dry-run"):
    s = datetime.now().isoformat()
    r = build(); d = r["phase153_onboarding_review_dashboard"]; b = d["board"]; js = b["judge_summary"]
    return {"phase153_onboarding_review_pipeline": {
        "mode": mode, "started_at": s, "finished_at": datetime.now().isoformat(),
        "candidates_reviewed": b["candidates_reviewed"],
        "ready_for_owner_approval": js.get("ready_for_owner_approval", 0),
        "needs_evidence_agent_follow_up": js.get("needs_evidence_agent_follow_up", 0),
        "needs_identity_confirmation": js.get("needs_identity_confirmation", 0),
        "blocked_for_now": js.get("blocked_for_now", 0),
        "quality_gate": d["quality_gate"]["overall_status"],
        "guard": d["guard"]["overall_status"],
        "cannot_conclude_guard": d["cannot_conclude_guard"]["overall_status"],
        "violations": d["guard"]["violations"],
        "research_only": True, "activation_allowed": False,
        "auto_add_to_watchlist_allowed": False, "auto_promote_to_core_allowed": False,
        "watch_core_updated": False, "candidate_auto_activated": False,
        "judge_pass_not_investment_approval": True,
        "onboarding_review_not_watch_activation": True,
        "mock_used": False, "fixture_used": False,
        "trade_recommendation_created": 0, "target_price_created": 0,
        "position_sizing_created": 0, "paper_order_created": 0, "paper_trade_created": 0,
        "broker_api_called": False, "llm_api_called": False,
    }}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true")
    p.add_argument("--skip-network", action="store_true"); p.add_argument("--json", action="store_true")
    a = p.parse_args()
    m = "execute" if a.execute else ("skip-network" if a.skip_network else "dry-run")
    print(json.dumps(run(m), indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__": main()
