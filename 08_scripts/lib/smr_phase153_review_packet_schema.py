def build_onboarding_review_packet_schema():
    return {"phase153_review_packet_schema": {
        "packet_types": ["identity", "source_route", "financial_route", "valuation_route",
                        "evidence_requirement", "risk_limitation", "initial_thesis_seed",
                        "owner_approval_checklist", "judge_agent_review"],
        "packet_structure": {
            "ticker": "string", "name": "string", "market": "string",
            "admission_score": "float", "review_packets": "dict",
            "judge_decision": "string", "onboarding_readiness": "string",
            "activation_eligibility": "string", "requires_owner_approval": "bool",
        },
        "route_ready_not_equal_to_data_loaded": True,
        "judge_pass_not_equal_to_investment_approval": True,
        "owner_approval_not_equal_to_trade_approval": True,
        "mock_used": False, "fixture_used": False,
    }}
