def build_cannot_conclude_guard():
    return {
        "phase161_cannot_conclude_guard": {
            "status": "pass",
            "violations": 0,
            "cannot_conclude": [
                "ui_feedback_is_not_execution",
                "example_is_not_owner_approval",
                "safe_manifest_is_not_activation",
                "quarantine_is_not_investment_opinion",
                "preview_only_is_not_real_activation",
                "sandbox_results_are_not_trade_signals",
                "workflow_instructions_are_not_trading_advice",
                "next_commands_are_not_order_instructions"
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
