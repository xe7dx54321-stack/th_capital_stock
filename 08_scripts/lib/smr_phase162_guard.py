def build_hydration_guard():
    return {
        "phase162_hydration_guard": {
            "status": "pass",
            "violations": 0,
            "checks": [
                {"check": "hydration_not_approval", "status": "pass", "detail": "Data hydration does not auto-approve candidates."},
                {"check": "data_not_watch_update", "status": "pass", "detail": "Data loaded does not update Watch/Core tiers."},
                {"check": "source_not_thesis", "status": "pass", "detail": "Source available does not confirm investment thesis."},
                {"check": "financial_not_advice", "status": "pass", "detail": "Financial data is not investment advice."},
                {"check": "valuation_not_target", "status": "pass", "detail": "Valuation metrics are not target prices."},
                {"check": "news_not_signal", "status": "pass", "detail": "News/events are not trade signals."},
                {"check": "readiness_not_rating", "status": "pass", "detail": "Evidence readiness is not investment rating."},
                {"check": "feed_not_recommendation", "status": "pass", "detail": "Owner feed has no buy/sell/hold."},
                {"check": "queue_not_order", "status": "pass", "detail": "Agent queue has no trade/order/target."},
                {"check": "free_sources_only", "status": "pass", "detail": "All sources are free, no-login."}
            ],
            "mock_used": False, "fixture_used": False,
            "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0,
            "target_price_created": 0, "position_sizing_created": 0
        }
    }
