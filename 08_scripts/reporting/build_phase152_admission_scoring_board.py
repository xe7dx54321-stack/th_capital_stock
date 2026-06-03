import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase152_loaders import load_phase151_discovery_queue
    from smr_phase152_composite_scorer import compute_composite_admission_score
    from smr_phase152_bucket_classifier import classify_admission_buckets
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

    return {"phase152_admission_scoring_board": {
        "scored_candidates": len(scored),
        "composite_scores": composite["phase152_composite_scorer"]["composite_scores"],
        "buckets": buckets["phase152_bucket_classifier"]["summary"],
        "bucket_details": buckets["phase152_bucket_classifier"]["buckets"],
        "admission_scoring_is_research_only": True,
        "admission_score_not_investment_rating": True,
        "admission_bucket_not_buy_sell": True,
        "mock_used": False, "fixture_used": False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
