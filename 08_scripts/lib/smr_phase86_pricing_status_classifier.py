def classify_pricing_status():
    """Self-contained: loads pricing data then classifies."""
    from smr_phase86_pricing_adapter import run_pricing_adapter
    pricing = run_pricing_adapter()
    pricing_rows = pricing["phase86_pricing_adapter"]["rows"]
    results = []
    for r in pricing_rows:
        ticker = r["ticker"]; mkt = r["market"]
        if not r.get("pricing_available", False):
            status = "blocked" if r.get("pricing_status") == "known_blocked" else "unavailable"
            results.append({"ticker": ticker, "market": mkt, "pricing_trend": status, "pricing_available": False, "current_price": None, "change_1mo": None, "classification_reason": r.get("blocker", "pricing_unavailable")})
            continue
        chg_1mo = r.get("change_1mo_pct"); chg_3mo = r.get("change_3mo_pct")
        trend = "range_bound"
        if chg_1mo is not None and chg_3mo is not None:
            if chg_1mo > 5 and chg_3mo > 5: trend = "trending_up_strong"
            elif chg_1mo > 2: trend = "trending_up"
            elif chg_1mo < -5 and chg_3mo < -5: trend = "trending_down_strong"
            elif chg_1mo < -2: trend = "trending_down"
            else: trend = "range_bound"
        elif chg_1mo is not None:
            if chg_1mo > 5: trend = "trending_up_strong"
            elif chg_1mo > 2: trend = "trending_up"
            elif chg_1mo < -5: trend = "trending_down_strong"
            elif chg_1mo < -2: trend = "trending_down"
        results.append({"ticker": ticker, "market": mkt, "pricing_trend": trend, "pricing_available": True, "current_price": r.get("current_price"), "change_1mo": chg_1mo, "change_3mo": chg_3mo, "classification_reason": f"1mo={chg_1mo}%, 3mo={chg_3mo}%"})
    return {"phase86_pricing_status_classifier": {"tickers_checked": len(results), "trending_up": sum(1 for r in results if "up" in r["pricing_trend"].lower()), "trending_down": sum(1 for r in results if "down" in r["pricing_trend"].lower()), "range_bound": sum(1 for r in results if r["pricing_trend"] == "range_bound"), "unavailable_or_blocked": sum(1 for r in results if not r["pricing_available"]), "rows": results, "mock_used": False, "fixture_used": False}}
