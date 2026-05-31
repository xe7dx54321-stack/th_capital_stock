from smr_phase86_config import load_config, get_target_tickers, get_known_blocked

def build_expectation_source_registry():
    c = load_config()
    rows = []
    blocked = get_known_blocked()
    for t in c["target_tickers"]:
        mkt = "CN_A"
        if t.endswith(".HK"): mkt = "HK"
        elif not (t.endswith(".SZ") or t.endswith(".SH")): mkt = "US"
        sources = c["expectation"]["sources"].get(mkt, [])
        blocked_flag = t in blocked
        rows.append({"ticker": t, "market": mkt, "sources": sources, "source_count": len(sources), "blocked": blocked_flag, "metrics_targeted": c["expectation"]["metrics"], "target_price_policy": c["expectation"]["target_price_policy"]})
    return {"phase86_expectation_source_registry": {"tickers_checked": len(rows), "total_sources_defined": sum(r["source_count"] for r in rows), "target_price_hidden": True, "rows": rows, "mock_used": False, "fixture_used": False}}
