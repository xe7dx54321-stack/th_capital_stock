def build_expectation_pricing_closeout():
    """Final closeout audit for Phase 86 combining pricing + expectation + valuation."""
    results = []
    # Load all data
    try:
        from smr_phase86_pricing_adapter import run_pricing_adapter
        pricing = run_pricing_adapter()
        pricing_rows = {r["ticker"]: r for r in pricing["phase86_pricing_adapter"]["rows"]}
    except: pricing_rows = {}
    try:
        from smr_phase86_expectation_adapter import run_expectation_adapter
        expectation = run_expectation_adapter()
        exp_rows = {r["ticker"]: r for r in expectation["phase86_expectation_adapter"]["rows"]}
    except: exp_rows = {}
    try:
        from smr_phase85b_closeout_audit import build_closeout_audit
        val_data = build_closeout_audit()
        val_rows = {r["ticker"]: r for r in val_data["phase85b_closeout_audit"]["rows"]}
    except: val_rows = {}
    for t in ["300308.SZ", "688041.SH", "002230.SZ", "300394.SZ", "09988.HK", "00700.HK", "NVDA", "AVGO"]:
        pr = pricing_rows.get(t, {}); er = exp_rows.get(t, {}); vr = val_rows.get(t, {})
        mkt = pr.get("market") or vr.get("market") or ""
        results.append({
            "ticker": t, "market": mkt,
            "pricing_status": pr.get("pricing_status", "N/A"), "pricing_available": pr.get("pricing_available", False),
            "expectation_status": er.get("expectation_status", "N/A"), "expectation_available": er.get("expectation_available", False),
            "valuation_status": vr.get("final_status", "N/A"), "valuation_available": vr.get("valuation_available", False),
            "current_price": pr.get("current_price"), "change_1mo": pr.get("change_1mo_pct"),
            "analyst_count": er.get("analyst_count"), "target_price_hidden": True
        })
    pricing_ok = sum(1 for r in results if r["pricing_available"])
    exp_ok = sum(1 for r in results if r["expectation_available"])
    val_ok = sum(1 for r in results if r["valuation_available"])
    blocked = sum(1 for r in results if r["valuation_status"] == "known_blocked")
    return {"phase86_expectation_pricing_closeout": {"tickers_total": len(results), "pricing_available": pricing_ok, "expectation_available": exp_ok, "valuation_available": val_ok, "blocked": blocked, "target_price_output_count": 0, "rows": results, "mock_used": False, "fixture_used": False}}
