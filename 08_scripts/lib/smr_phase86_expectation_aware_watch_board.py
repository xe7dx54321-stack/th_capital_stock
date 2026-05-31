def build_expectation_aware_watch_board():
    """Expectation-aware watch board combining all signals."""
    from smr_phase86_closeout_audit import build_expectation_pricing_closeout
    data = build_expectation_pricing_closeout()
    rows = data["phase86_expectation_pricing_closeout"]["rows"]
    sections = {"pricing_trend_up": [], "pricing_trend_down": [], "pricing_flat": [], "expectation_available": [], "expectation_unavailable": [], "blocked": []}
    for r in rows:
        t = r["ticker"]
        if r["valuation_status"] == "known_blocked":
            sections["blocked"].append({"ticker": t, "market": r["market"], "section": "blocked", "blocker": "cninfo_org_id_missing"})
            continue
        if r["expectation_available"]:
            sections["expectation_available"].append({"ticker": t, "market": r["market"], "section": "expectation_available", "analyst_count": r.get("analyst_count"), "target_price_hidden": True})
        elif r["expectation_status"] == "expectation_unavailable_with_exhausted_sources":
            sections["expectation_unavailable"].append({"ticker": t, "market": r["market"], "section": "expectation_unavailable", "reason": "sources_exhausted"})
        chg = r.get("change_1mo")
        if chg is not None and chg > 2:
            sections["pricing_trend_up"].append({"ticker": t, "market": r["market"], "section": "pricing_trend_up", "change_1mo": chg})
        elif chg is not None and chg < -2:
            sections["pricing_trend_down"].append({"ticker": t, "market": r["market"], "section": "pricing_trend_down", "change_1mo": chg})
        else:
            sections["pricing_flat"].append({"ticker": t, "market": r["market"], "section": "pricing_flat", "change_1mo": chg})
    return {"phase86_expectation_aware_watch_board": {"tickers_total": len(rows), "sections": {k: len(v) for k, v in sections.items()}, "rows": rows, "target_price_output_count": 0, "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0}}
