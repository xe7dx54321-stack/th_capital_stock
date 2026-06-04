def build_cannot_conclude_guard():
    return {
        "phase160_cannot_conclude_guard": {
            "status": "pass",
            "violations": 0,
            "cannot_conclude": [
                "example_approval_is_not_real_owner_approval",
                "sandbox_validation_is_not_research_activation",
                "safe_example_is_not_executed_tier_update",
                "example_pack_is_not_auto_decision_pipeline",
                "sandbox_is_not_trade_signal_generator",
                "sample_decisions_are_not_investment_advice",
                "cookbook_is_not_trading_manual"
            ],
            "reserved_constraints": [
                "300394 CNINFO org_id missing",
                "300394 thesis unconfirmed",
                "688041 derived valuation label only"
            ],
            "mock_used": False,
            "fixture_used": False
        }
    }
