from smr_phase85b_closeout_config import load_config, get_problem_tickers, get_preserved_blocked

def build_fallback_registry():
    c = load_config()
    rows = []
    for pt in c["problem_tickers"]:
        sources = []
        for fp in pt["fallback_priority"]:
            if fp.startswith("yfinance_"):
                sym = fp.replace("yfinance_", "").replace("_SH", ".SH").replace("_HK", ".HK").replace("_", ".")
                if sym == "BABA.ADR.proxy": sym = "BABA"
                if sym == "TCEHY.ADR.proxy": sym = "TCEHY"
                sources.append({"source_name": "yfinance_info", "source_ticker_format": sym, "source_type": "api", "requires_network": True, "used_for": ["market_cap", "pe_ttm", "ps_ttm", "pb"]})
            elif fp.startswith("akshare_"):
                src_name = fp.replace("akshare_", "")
                sources.append({"source_name": "akshare", "source_function": src_name, "source_type": "api", "requires_network": True, "used_for": ["market_cap", "pe_ttm", "ps_ttm", "pb"]})
            elif fp.startswith("derived_"):
                sources.append({"source_name": "derived_valuation", "source_function": "derive_from_financial_data", "source_type": "computed", "requires_network": False, "used_for": ["ps_derived", "pe_derived", "pb_derived"]})
        rows.append({"ticker": pt["ticker"], "market": pt["market"], "original_status": pt["original_status"], "fallback_sources": sources, "source_count": len(sources)})
    blocked = get_preserved_blocked()
    for b in blocked:
        rows.append({"ticker": b, "market": "CN_A", "original_status": "known_blocked", "fallback_sources": [], "source_count": 0, "preserved": True})
    return {"phase85b_fallback_registry": {"tickers_checked": len(rows), "has_fallback": sum(1 for r in rows if r["source_count"] > 0), "preserved_blocked": len(blocked), "rows": rows, "mock_used": False, "fixture_used": False}}
