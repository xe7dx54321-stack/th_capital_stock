def build_cannot_conclude_guard():
    return {
        "phase162_cannot_conclude_guard": {
            "status": "pass",
            "violations": 0,
            "cannot_conclude": [
                "hydration_is_not_owner_approval",
                "data_loaded_is_not_watch_update",
                "source_available_is_not_thesis_confirmed",
                "financial_data_is_not_investment_advice",
                "valuation_is_not_target_price",
                "news_event_is_not_trade_signal",
                "evidence_readiness_is_not_investment_rating",
                "owner_feed_is_not_buy_sell_hold",
                "agent_queue_is_not_trade_order",
                "skip_network_status_is_not_permanent_block"
            ],
            "reserved_constraints": [
                "300394 CNINFO org_id missing",
                "300394 thesis unconfirmed",
                "688041 derived valuation label only"
            ],
            "mock_used": False, "fixture_used": False
        }
    }
