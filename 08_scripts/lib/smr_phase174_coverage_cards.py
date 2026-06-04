# Phase174 coverage cards - per-candidate post-apply view
from smr_phase174_coverage_state_registry import build_coverage_state_registry

def build_coverage_cards():
    registry = build_coverage_state_registry()
    r = registry["phase174_coverage_state_registry"]
    cards = []
    for e in r["entries"]:
        cid = e["candidate_id"]
        tier = e["coverage_tier"]
        card = {
            "candidate_id":cid,
            "coverage_tier":tier,
            "owner_decision":e["owner_decision"],
            "rationale":e["rationale"],
            "conditions":e["conditions"],
            "risk_acknowledgment":e["risk_acknowledgment"],
            "daily_monitoring_eligible":e["daily_monitoring_eligible"],
            "weekly_review_eligible":e["weekly_review_eligible"],
            "agent_task_eligible":e["agent_task_eligible"],
            "monitoring_status":"active" if tier=="formal_research_coverage" else ("pending" if tier=="candidate_pending" else "inactive"),
            "post_apply_note":"Formal research coverage active. Daily monitoring and agent tasks enabled." if tier=="formal_research_coverage" else "Not yet in formal research coverage. Review at next cycle."
        }
        cards.append(card)
    return {"phase174_coverage_cards":{
        "cards_count":len(cards),"cards":cards,
        "research_only":True,"not_trade_cards":True,
        "mock_used":False,"fixture_used":False
    }}
