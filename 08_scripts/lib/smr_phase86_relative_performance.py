from smr_phase86_config import get_indices, get_ticker_format
from smr_phase86_pricing_adapter import fetch_price_data

def compute_relative_performance():
    """Compute performance relative to market indices."""
    results = []; indices = get_indices()
    # Fetch index data
    idx_perf = {}
    for market, idx_sym in indices.items():
        data = fetch_price_data(idx_sym, idx_sym)
        idx_perf[market] = {"1mo": data.get("change_1mo_pct"), "3mo": data.get("change_3mo_pct"), "6mo": data.get("change_6mo_pct"), "available": data["price_available"]}
    # Compute for each ticker
    from smr_phase86_pricing_adapter import run_pricing_adapter
    pricing = run_pricing_adapter()
    for r in pricing["phase86_pricing_adapter"]["rows"]:
        mkt = r["market"]
        idx_data = idx_perf.get(mkt, {})
        rel = {}
        if r["pricing_available"] and idx_data.get("available"):
            for period in ["1mo", "3mo", "6mo"]:
                ticker_pct = r.get(f"change_{period}_pct"); idx_pct = idx_data.get(period)
                if ticker_pct is not None and idx_pct is not None:
                    rel[f"rel_{period}"] = round(ticker_pct - idx_pct, 2)
        results.append({"ticker": r["ticker"], "market": mkt, "pricing_available": r["pricing_available"], "relative_performance": rel, "index_used": {"CN_A": "000300.SS", "HK": "^HSI", "US": "^GSPC"}.get(mkt, ""), "index_available": idx_data.get("available", False)})
    return {"phase86_relative_performance": {"tickers_checked": len(results), "index_data_available": sum(1 for v in idx_perf.values() if v["available"]), "rows": results, "mock_used": False, "fixture_used": False}}
