def build_evidence_freshness_completeness_validator(normalizer_output, mode="dry-run"):
    norm = normalizer_output["phase166_live_evidence_normalizer"]["results"]
    results = []
    for entry in norm:
        ev_types = ["quote_normalized","financial_normalized","valuation_normalized","news_normalized","filing_normalized","transcript_normalized"]
        filled_count = sum(1 for k in ev_types if entry.get(k, False))
        completeness = filled_count / len(ev_types) if len(ev_types) > 0 else 0
        results.append({
            "ticker": entry["ticker"],
            "filled_count": filled_count,
            "total_types": len(ev_types),
            "completeness_ratio": round(completeness, 2),
            "freshness": "live" if mode == "execute" else "planned",
            "freshness_not_quality_rating": True,
            "completeness_not_investment_rating": True,
            "cannot_conclude": ["freshness_is_not_data_quality_rating", "completeness_is_not_investment_rating", "validator_output_is_not_trade_signal"]
        })
    avg_completeness = sum(r["completeness_ratio"] for r in results) / len(results) if results else 0
    return {
        "phase166_evidence_freshness_completeness_validator": {
            "candidates": len(results),
            "average_completeness": round(avg_completeness, 2),
            "freshness_not_trade_signal": True,
            "completeness_not_investment_rating": True,
            "results": results,
            "mock_used": False,
            "fixture_used": False
        }
    }
