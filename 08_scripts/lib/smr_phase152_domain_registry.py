def build_phase152_domain_registry():
    return {
        "phase152_domain_registry": {
            "domains": [
                {"domain": "admission_scoring", "description": "Candidate admission scoring system", "status": "active"},
            ],
            "cross_phase_dependencies": [
                {"phase": "phase151", "dependency": "discovery_queue", "usage": "load candidates for scoring"},
                {"phase": "phase150", "dependency": "tier_assignments", "usage": "check capacity"},
                {"phase": "phase149", "dependency": "agent_instructions", "usage": "route to agents"},
                {"phase": "phase148", "dependency": "activation_plans", "usage": "estimate effort"},
            ],
            "mock_used": False, "fixture_used": False,
        }
    }
