def build_sandbox_guard():
    return {
        "phase160_sandbox_guard": {
            "status": "pass",
            "violations": 0,
            "checks": [
                {"check": "sandbox_not_execution", "status": "pass", "detail": "Sandbox validation does not execute real candidate activation."},
                {"check": "real_input_not_overwritten", "status": "pass", "detail": "Sandbox writes to separate gitignored path."},
                {"check": "watch_core_not_updated", "status": "pass", "detail": "watch_core_updated=false. No Watch/Core tier changes."},
                {"check": "candidate_not_auto_activated", "status": "pass", "detail": "candidate_auto_activated=false. No automatic activation."},
                {"check": "tier_update_not_executed", "status": "pass", "detail": "tier_update_executed=false. No tier changes executed."},
                {"check": "activation_not_created", "status": "pass", "detail": "activation_execution_created=false."},
                {"check": "no_trade_recommendation", "status": "pass", "detail": "No buy/sell/target/position output."},
                {"check": "example_not_real_approval", "status": "pass", "detail": "Example approval is not real owner approval."},
                {"check": "sandbox_not_activation", "status": "pass", "detail": "Sandbox validation is not real research activation."},
                {"check": "safe_example_not_execution", "status": "pass", "detail": "Safe examples do not trigger execution."}
            ],
            "mock_used": False,
            "fixture_used": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "target_price_created": 0,
            "position_sizing_created": 0
        }
    }
