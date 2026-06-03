def build_admission_scoring_schema():
    return {
        "phase152_admission_scoring_schema": {
            "score_range": {"min": 0.0, "max": 5.0},
            "dimensions": [
                {"id": "identity_confidence", "weight": 1.0},
                {"id": "source_availability", "weight": 1.0},
                {"id": "financial_route_readiness", "weight": 1.0},
                {"id": "valuation_route_readiness", "weight": 1.0},
                {"id": "theme_fit", "weight": 1.5},
                {"id": "evidence_readiness", "weight": 1.0},
                {"id": "catalyst_novelty", "weight": 1.0},
                {"id": "risk_limitation_penalty", "weight": -0.5},
                {"id": "capacity_fit", "weight": 1.0},
                {"id": "owner_relevance", "weight": 1.0},
                {"id": "activation_effort", "weight": 0.5},
            ],
            "admission_buckets": {
                "admit_to_onboarding_review": {"min_score": 3.5},
                "watch_for_more_evidence": {"min_score": 2.5},
                "manual_identity_or_source_review": {"min_score": 1.5},
                "defer": {"min_score": 0.5},
                "reject_for_now": {"min_score": 0.0},
            },
            "mock_used": False, "fixture_used": False,
        }
    }
