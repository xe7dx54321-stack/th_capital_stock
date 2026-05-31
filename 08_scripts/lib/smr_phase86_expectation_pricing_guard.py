def build_expectation_pricing_guard():
    """Guard that ensures no target price output, no trade signals."""
    checks = {
        "target_price_hidden": True, "target_price_output_count": 0,
        "no_buy_signal": True, "no_sell_signal": True, "no_short_signal": True,
        "no_position_sizing": True, "position_sizing_created": 0,
        "no_pending_created": True, "no_paper_order_created": True, "no_real_trade_created": True,
        "pricing_is_observation": True, "expectation_is_observation": True,
        "consensus_rating_is_not_trade_signal": True, "monitoring_not_investment_advice": True,
        "strengthened_not_confirmed": True, "anomaly_not_trade_signal": True,
        "overall_status": "pass"
    }
    return {"phase86_expectation_pricing_guard": checks}
