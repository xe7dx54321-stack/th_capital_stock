def build_evidence_review_packet(candidate):
    source = candidate.get("discovery_source", ""); market = candidate.get("market", "")
    if source in ("theme_based", "peer_based", "industry_chain"): status = "structural_anchor_exists"
    elif source in ("news_event", "financial_change"): status = "evidence_limited_recent"
    elif source == "customer_capex": status = "capex_anchor"
    else: status = "evidence_not_built"
    return {"packet_type": "evidence_requirement_review", "ticker": candidate["ticker"],
        "evidence_status": status,
        "required_evidence": ["public_filings", "industry_context", "thesis_statement"],
        "notes": [f"Evidence status: {status}"],
        "cannot_conclude": ["evidence_chain_not_built", "sources_not_verified"],
        "mock_used": False, "fixture_used": False}
