def build_phase160_domain_registry():
    return {
        "phase160_domain_registry": {
            "domains": [
                {"domain": "owner_decision_example_pack", "description": "Owner decision example pack generation", "status": "active"},
                {"domain": "safe_input_sandbox", "description": "Safe input sandbox for validation testing", "status": "active"},
                {"domain": "example_validation", "description": "Example-to-Phase159 compatibility validation", "status": "active"}
            ],
            "mock_used": False,
            "fixture_used": False
        }
    }
