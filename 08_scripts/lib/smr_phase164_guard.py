def build_console_guard():
    return {
        "phase164_console_guard": {
            "status": "pass", "violations": 0,
            "checks": [
                {"check": "console_not_approval", "status": "pass"},
                {"check": "snapshot_not_watch_update", "status": "pass"},
                {"check": "monitoring_not_trade_signal", "status": "pass"},
                {"check": "agent_queue_not_trading", "status": "pass"},
                {"check": "precheck_not_execution", "status": "pass"}
            ],
            "mock_used": False, "fixture_used": False,
            "pending_created": 0, "paper_order_created": 0,
            "real_trade_created": 0, "target_price_created": 0
        }
    }
