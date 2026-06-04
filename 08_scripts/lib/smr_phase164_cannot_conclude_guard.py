def build_cannot_conclude_guard():
    return {
        "phase164_cannot_conclude_guard": {
            "status": "pass", "violations": 0,
            "cannot_conclude": [
                "console_is_not_owner_approval",
                "snapshot_is_not_watch_update",
                "monitoring_is_not_trade_signal",
                "agent_queue_is_not_trading",
                "precheck_is_not_execution",
                "scheduler_is_not_real_registration"
            ],
            "reserved_constraints": [
                "300394 CNINFO org_id missing",
                "300394 thesis unconfirmed",
                "688041 derived valuation label only"
            ],
            "mock_used": False, "fixture_used": False
        }
    }
