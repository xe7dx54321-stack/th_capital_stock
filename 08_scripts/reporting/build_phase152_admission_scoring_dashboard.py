import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase152_config import load_phase152_config
    from build_phase152_admission_scoring_board import build as build_board
    from smr_phase152_quality_gate import run_phase152_quality_gate
    from smr_phase152_guard import run_phase152_admission_guard
    from smr_phase152_cannot_conclude_guard import run_phase152_cannot_conclude_guard
    from smr_phase152_next_action_planner import plan_admission_next_actions
    from smr_phase152_bucket_classifier import classify_admission_buckets
    from smr_phase152_composite_scorer import compute_composite_admission_score
    from smr_phase152_agent_routing import build_agent_routing
    from smr_phase152_backlog import build_phase152_backlog
    from smr_phase152_loaders import load_phase151_discovery_queue
    from smr_phase152_identity_scorer import score_identity_confidence
    from smr_phase152_source_scorer import score_source_availability
    from smr_phase152_financial_scorer import score_financial_route_readiness
    from smr_phase152_valuation_scorer import score_valuation_route_readiness
    from smr_phase152_theme_scorer import score_theme_fit
    from smr_phase152_evidence_scorer import score_evidence_readiness
    from smr_phase152_catalyst_scorer import score_catalyst_novelty
    from smr_phase152_risk_scorer import score_risk_penalty
    from smr_phase152_capacity_scorer import score_capacity_fit
    from smr_phase152_owner_scorer import score_owner_relevance
    from smr_phase152_effort_scorer import score_activation_effort

    queue = load_phase151_discovery_queue()
    candidates = queue.get("queue", [])
    scored = []
    for c in candidates:
        sc = {"ticker": c["ticker"], "name": c.get("name", ""), "market": c.get("market", ""),
              "discovery_source": c.get("discovery_source", ""), "priority": c.get("priority", ""),
              "scores": {
                  "identity_confidence": score_identity_confidence(c),
                  "source_availability": score_source_availability(c),
                  "financial_route_readiness": score_financial_route_readiness(c),
                  "valuation_route_readiness": score_valuation_route_readiness(c),
                  "theme_fit": score_theme_fit(c),
                  "evidence_readiness": score_evidence_readiness(c),
                  "catalyst_novelty": score_catalyst_novelty(c),
                  "risk_limitation_penalty": score_risk_penalty(c),
                  "capacity_fit": score_capacity_fit(c),
                  "owner_relevance": score_owner_relevance(c),
                  "activation_effort": score_activation_effort(c),
              }}
        scored.append(sc)

    composite = compute_composite_admission_score(scored)
    buckets = classify_admission_buckets(composite["phase152_composite_scorer"])
    actions = plan_admission_next_actions(buckets["phase152_bucket_classifier"])
    routing = build_agent_routing(composite["phase152_composite_scorer"], buckets["phase152_bucket_classifier"])
    gate = run_phase152_quality_gate()
    guard = run_phase152_admission_guard()
    cc_guard = run_phase152_cannot_conclude_guard(composite["phase152_composite_scorer"])
    backlog = build_phase152_backlog(buckets["phase152_bucket_classifier"])

    return {"phase152_admission_scoring_dashboard": {
        "config": load_phase152_config(),
        "board": build_board()["phase152_admission_scoring_board"],
        "quality_gate": gate["phase152_quality_gate"],
        "guard": guard["phase152_admission_guard"],
        "cannot_conclude_guard": cc_guard["phase152_cannot_conclude_guard"],
        "next_actions": actions["phase152_next_action_planner"],
        "agent_routing": routing["phase152_agent_routing"],
        "backlog": backlog["phase152_backlog"],
        "research_only": True,
        "auto_add_to_watchlist_allowed": False, "auto_promote_to_core_allowed": False,
        "mock_used": False, "fixture_used": False,
        "trade_recommendation_created": 0, "paper_order_created": 0, "paper_trade_created": 0,
        "target_price_created": 0, "position_sizing_created": 0,
        "broker_api_called": False, "llm_api_called": False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
