def build_thesis_seed_review_packet(candidate):
    trigger = candidate.get("trigger", ""); source = candidate.get("discovery_source", "")
    if source == "theme_based": seed = f"Thematic alignment: {trigger}"
    elif source == "peer_based": seed = f"Peer to covered ticker: {trigger}"
    elif source == "industry_chain": seed = f"Industry chain: {trigger}"
    elif source == "customer_capex": seed = f"Capex beneficiary: {trigger}"
    else: seed = f"Discovered via {source}: {trigger}"
    return {"packet_type": "initial_thesis_seed_review", "ticker": candidate["ticker"],
        "thesis_seed": seed, "thesis_status": "unconfirmed",
        "notes": ["Thesis seed is unconfirmed; requires evidence build and manual review"],
        "cannot_conclude": ["thesis_not_confirmed", "specific_customer_or_order_data_not_available"],
        "mock_used": False, "fixture_used": False}
