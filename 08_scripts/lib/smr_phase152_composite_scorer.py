def compute_composite_admission_score(scored_candidates):
    weights = {
        "identity_confidence": 1.0, "source_availability": 1.0,
        "financial_route_readiness": 1.0, "valuation_route_readiness": 1.0,
        "theme_fit": 1.5, "evidence_readiness": 1.0, "catalyst_novelty": 1.0,
        "risk_limitation_penalty": -0.5, "capacity_fit": 1.0,
        "owner_relevance": 1.0, "activation_effort": 0.5,
    }
    results = []
    for c in scored_candidates:
        scores = c.get("scores", {})
        weighted_sum = 0.0; weight_sum = 0.0
        for dim, w in weights.items():
            dim_score = scores.get(dim, {}).get("score", 0.0)
            weighted_sum += dim_score * abs(w); weight_sum += abs(w)
        composite = round(weighted_sum / weight_sum, 2) if weight_sum > 0 else 0.0
        results.append({"ticker": c["ticker"], "name": c.get("name", ""), "market": c.get("market", ""),
                        "composite_score": composite, "max_composite_score": 5.0, "scores": scores})
    return {"phase152_composite_scorer": {"scored_candidates_count": len(results), "composite_scores": results,
                                          "mock_used": False, "fixture_used": False}}
