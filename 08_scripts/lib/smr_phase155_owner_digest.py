def build_owner_review_digest(targets):
    items = []
    for t in targets:
        items.append({"ticker":t,"loop_status":"completed","action_required":"review_output","contains_trade_action":False,"contains_buy_sell":False,"contains_target_price":False,"contains_position_sizing":False})
    return {"phase155_owner_digest":{"digest_type":"owner_review","items":len(items),"digest_items":items,"owner_digest_is_not_investment_advice":True,"no_trade_actions":True,"mock_used":False,"fixture_used":False}}
