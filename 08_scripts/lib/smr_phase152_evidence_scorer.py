def score_evidence_readiness(candidate):
    source = candidate.get("discovery_source", ""); market = candidate.get("market", "")
    if source in ("theme_based", "peer_based", "industry_chain"): score = 3.5; notes = ["thematic/peer/chain anchor"]
    elif source in ("news_event", "financial_change"): score = 2.5; notes = ["event-driven, evidence limited"]
    elif source == "customer_capex": score = 3.0; notes = ["capex-based anchor"]
    elif source == "external_public_lists": score = 2.0; notes = ["evidence chain not built"]
    else: score = 2.5; notes = ["evidence readiness unverified"]
    if market in ("HK", "CN_A"): score = max(score - 0.5, 1.0); notes.append("non-US market may have fewer public filings")
    return {
        "dimension": "evidence_readiness", "score": score, "max_score": 5.0, "notes": notes,
        "cannot_conclude": ["evidence_chain_not_built"],
        "mock_used": False, "fixture_used": False,
    }
