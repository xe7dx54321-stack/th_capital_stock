def build_owner_action_proposal(targets):
    proposals = []
    for t in targets:
        proposals.append({"ticker": t, "action_type": "review_research_output",
                         "action_description": f"Review loop output for {t} and decide on activation.",
                         "contains_trade_action": False, "contains_buy_sell": False,
                         "contains_target_price": False, "contains_position_sizing": False,
                         "requires_owner_sign_off": True})
    return {"phase154_owner_action_proposal": {"proposals": len(proposals), "actions": proposals,
        "owner_actions_are_review_only": True, "no_trade_actions": True,
        "mock_used": False, "fixture_used": False}}
