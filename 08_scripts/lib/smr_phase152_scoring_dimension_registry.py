def build_scoring_dimension_registry():
    return {
        "phase152_scoring_dimension_registry": {
            "dimension_count": 11,
            "dimensions": [
                {"id": "identity_confidence", "score_range": "0-5", "higher_is_better": True, "auto_scorable": True},
                {"id": "source_availability", "score_range": "0-5", "higher_is_better": True, "auto_scorable": True},
                {"id": "financial_route_readiness", "score_range": "0-5", "higher_is_better": True, "auto_scorable": True},
                {"id": "valuation_route_readiness", "score_range": "0-5", "higher_is_better": True, "auto_scorable": True},
                {"id": "theme_fit", "score_range": "0-5", "higher_is_better": True, "auto_scorable": True},
                {"id": "evidence_readiness", "score_range": "0-5", "higher_is_better": True, "auto_scorable": True},
                {"id": "catalyst_novelty", "score_range": "0-5", "higher_is_better": True, "auto_scorable": False},
                {"id": "risk_limitation_penalty", "score_range": "0-5", "higher_is_better": False, "auto_scorable": True},
                {"id": "capacity_fit", "score_range": "0-5", "higher_is_better": True, "auto_scorable": True},
                {"id": "owner_relevance", "score_range": "0-5", "higher_is_better": True, "auto_scorable": False},
                {"id": "activation_effort", "score_range": "0-5", "higher_is_better": False, "auto_scorable": True},
            ],
            "mock_used": False, "fixture_used": False,
        }
    }
