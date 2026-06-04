def build_phase162_domain_registry():
    return {
        "phase162_domain_registry": {
            "domains": [
                {"domain": "candidate_identity_resolution", "description": "Resolve candidate ticker identity", "status": "active"},
                {"domain": "candidate_source_route_planning", "description": "Plan free no-login data sources per candidate", "status": "active"},
                {"domain": "candidate_data_hydration", "description": "Hydrate candidate data: quote, financial, valuation, news", "status": "active"},
                {"domain": "candidate_evidence_readiness", "description": "Score candidate readiness for research activation", "status": "active"}
            ],
            "mock_used": False,
            "fixture_used": False
        }
    }
