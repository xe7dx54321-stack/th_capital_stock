import json, sys, os, argparse
from pathlib import Path
from datetime import datetime
BASE_LIB = Path(__file__).resolve().parent.parent / "lib"
BASE_REPORTING = Path(__file__).resolve().parent.parent / "reporting"
sys.path.insert(0, str(BASE_LIB))
sys.path.insert(0, str(BASE_REPORTING))
from build_phase152_admission_scoring_dashboard import build

def run(mode="dry-run"):
    s = datetime.now().isoformat()
    r = build()
    d = r["phase152_admission_scoring_dashboard"]
    board = d["board"]
    bsum = board["buckets"]
    return {"phase152_admission_scoring_pipeline": {
        "mode": mode, "started_at": s, "finished_at": datetime.now().isoformat(),
        "scored_candidates": board["scored_candidates"],
        "admit_to_onboarding_review": bsum.get("admit_to_onboarding_review", 0),
        "watch_for_more_evidence": bsum.get("watch_for_more_evidence", 0),
        "manual_identity_or_source_review": bsum.get("manual_identity_or_source_review", 0),
        "defer": bsum.get("defer", 0),
        "reject_for_now": bsum.get("reject_for_now", 0),
        "quality_gate": d["quality_gate"]["overall_status"],
        "guard": d["guard"]["overall_status"],
        "cannot_conclude_guard": d["cannot_conclude_guard"]["overall_status"],
        "violations": d["guard"]["violations"],
        "agent_routing": {
            "evidence_agent": d["agent_routing"]["evidence_agent"]["candidates_routed"],
            "risk_agent": d["agent_routing"]["risk_agent"]["candidates_routed"],
            "judge_agent": d["agent_routing"]["judge_agent"]["candidates_routed"],
        },
        "research_only": True,
        "auto_add_to_watchlist_allowed": False, "auto_promote_to_core_allowed": False,
        "admission_score_not_investment_rating": True, "admission_bucket_not_buy_sell": True,
        "mock_used": False, "fixture_used": False,
        "trade_recommendation_created": 0, "paper_order_created": 0, "paper_trade_created": 0,
        "target_price_created": 0, "position_sizing_created": 0,
        "broker_api_called": False, "llm_api_called": False,
    }}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--skip-network", action="store_true")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    m = "execute" if a.execute else ("skip-network" if a.skip_network else "dry-run")
    print(json.dumps(run(m), indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    main()
