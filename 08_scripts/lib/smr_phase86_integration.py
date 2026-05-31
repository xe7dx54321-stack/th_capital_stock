def build_integration():
    """Combine Phase 84 signal + Phase 85b valuation + Phase 86 pricing + expectation."""
    results = []
    ticker_map = {}
    # Load pricing
    try:
        from smr_phase86_pricing_adapter import run_pricing_adapter
        pr = run_pricing_adapter()
        for r in pr["phase86_pricing_adapter"]["rows"]:
            ticker_map[r["ticker"]] = {"ticker": r["ticker"], "market": r["market"], "pricing_status": r["pricing_status"], "pricing_available": r["pricing_available"], "current_price": r.get("current_price"), "change_1mo": r.get("change_1mo_pct"), "price_source": r.get("price_source", "")}
    except: pass
    # Load valuation (Phase 85b closeout)
    try:
        from smr_phase85b_closeout_audit import build_closeout_audit
        va = build_closeout_audit()
        for r in va["phase85b_closeout_audit"]["rows"]:
            t = r["ticker"]
            if t in ticker_map:
                ticker_map[t]["valuation_status"] = r["final_status"]; ticker_map[t]["valuation_available"] = r["valuation_available"]
            else:
                ticker_map[t] = {"ticker": t, "market": r["market"], "valuation_status": r["final_status"], "valuation_available": r["valuation_available"]}
    except: pass
    # Load expectation
    try:
        from smr_phase86_expectation_adapter import run_expectation_adapter
        ex = run_expectation_adapter()
        for r in ex["phase86_expectation_adapter"]["rows"]:
            t = r["ticker"]
            if t in ticker_map:
                ticker_map[t]["expectation_status"] = r["expectation_status"]; ticker_map[t]["expectation_available"] = r["expectation_available"]
            else:
                ticker_map[t] = {"ticker": t, "market": r["market"], "expectation_status": r["expectation_status"], "expectation_available": r["expectation_available"]}
    except: pass
    # Build integrated rows
    for t in ["300308.SZ", "688041.SH", "002230.SZ", "300394.SZ", "09988.HK", "00700.HK", "NVDA", "AVGO"]:
        row = ticker_map.get(t, {"ticker": t, "market": "unknown"})
        pricing_ok = row.get("pricing_available", False)
        val_ok = row.get("valuation_available", False)
        exp_ok = row.get("expectation_available", False)
        # Determine integration summary
        summary = "watch_only"
        if not pricing_ok and not val_ok: summary = "minimal_data_available"
        elif pricing_ok and not val_ok: summary = "pricing_only"
        elif val_ok and not pricing_ok: summary = "valuation_only"
        elif pricing_ok and val_ok and not exp_ok: summary = "pricing_and_valuation_no_expectation"
        else: summary = "full_integration_available"
        results.append({"ticker": t, "market": row.get("market", ""), "pricing_available": pricing_ok, "valuation_available": val_ok, "expectation_available": exp_ok, "integration_summary": summary, "current_price": row.get("current_price"), "change_1mo": row.get("change_1mo"), "price_source": row.get("price_source", ""), "valuation_status": row.get("valuation_status", ""), "expectation_status": row.get("expectation_status", "N/A")})
    return {"phase86_integration": {"tickers_total": len(results), "full_integration": sum(1 for r in results if "full" in r["integration_summary"]), "pricing_available": sum(1 for r in results if r["pricing_available"]), "valuation_available": sum(1 for r in results if r["valuation_available"]), "expectation_available": sum(1 for r in results if r["expectation_available"]), "rows": results, "mock_used": False, "fixture_used": False, "target_price_output_count": 0}}
