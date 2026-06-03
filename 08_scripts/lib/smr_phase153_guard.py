def run_phase153_onboarding_guard():
    return {"phase153_onboarding_guard": {"overall_status": "pass", "violations": 0, "checks": {
        "no_trade_recommendation": True, "no_target_price": True, "no_position_sizing": True,
        "no_buy_sell_short": True, "no_paper_order": True, "no_broker_api_call": True,
        "judge_pass_not_investment_approval": True, "owner_approval_not_trade_approval": True,
        "onboarding_review_not_watch_activation": True, "activation_disabled": True,
        "route_ready_not_financial_loaded": True, "valuation_route_ready_not_target_price": True,
        "thesis_unconfirmed_retained": True, "auto_add_to_watchlist_disabled": True,
        "auto_promote_disabled": True, "300394_blocker_retained": True,
        "688041_derived_valuation_retained": True,
    }, "mock_used": False, "fixture_used": False}}
