# Phase174 weekly review plan
from smr_phase174_coverage_state_registry import build_coverage_state_registry

def build_weekly_review_plan():
    registry = build_coverage_state_registry()
    r = registry["phase174_coverage_state_registry"]
    weekly_entries = [e for e in r["entries"] if e["weekly_review_eligible"]]
    plans = []
    for e in weekly_entries:
        tier_label = "active_coverage" if e["coverage_tier"]=="formal_research_coverage" else "candidate_pending_review"
        plans.append({
            "candidate_id":e["candidate_id"],
            "coverage_tier":e["coverage_tier"],
            "review_type":tier_label,
            "check_items":["thesis_review","evidence_update","agent_task_status","coverage_drift_check"],
            "cannot_conclude":["weekly_review_is_not_trade_rebalance","review_not_recommendation"]
        })
    return {"phase174_weekly_review_plan":{
        "weekly_review_enabled":True,
        "eligible_candidates":len(weekly_entries),
        "plans":plans,
        "review_not_trade":True,
        "mock_used":False,"fixture_used":False
    }}
