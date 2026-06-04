def update_owner_review_feed(targets, readiness):
    readiness_map = {r["ticker"]: r for r in readiness["phase162_evidence_readiness_scorer"]["results"]}
    items = []
    for t in targets:
        ticker = t.get("ticker", "")
        r = readiness_map.get(ticker, {})
        items.append({
            "ticker": ticker,
            "name": t.get("name", ""),
            "readiness_tier": r.get("readiness_tier", "unknown"),
            "hydration_status": "partial_hydration_ready",
            "recommended_owner_action": "review_data_readiness",
            "no_buy_sell_hold": True,
            "no_trade_recommendation": True
        })
    return {
        "phase162_owner_review_feed": {
            "items": len(items),
            "full_readiness": sum(1 for i in items if i["readiness_tier"] == "full"),
            "partial_readiness": sum(1 for i in items if i["readiness_tier"] == "partial"),
            "no_buy_sell_hold_language": True,
            "no_trade_recommendation": True,
            "feed_items": items,
            "mock_used": False,
            "fixture_used": False
        }
    }
