from smr_phase86_config import load_config, get_target_tickers, get_known_blocked

def build_pricing_source_registry():
    c = load_config()
    rows = []
    blocked = get_known_blocked()
    for t in c["target_tickers"]:
        mkt = "CN_A"
        if t.endswith(".HK"): mkt = "HK"
        elif not (t.endswith(".SZ") or t.endswith(".SH")): mkt = "US"
        sources = c["pricing"]["sources"].get(mkt, [])
        fmt = c["pricing"]["ticker_format_map"].get(t, t)
        blocked_flag = t in blocked
        rows.append({"ticker": t, "market": mkt, "yfinance_symbol": fmt, "sources": sources, "source_count": len(sources), "blocked_for_fundamental": blocked_flag, "pricing_blocked": False})
    return {"phase86_pricing_source_registry": {"tickers_checked": len(rows), "sources_defined": sum(r["source_count"] for r in rows), "rows": rows, "mock_used": False, "fixture_used": False}}
