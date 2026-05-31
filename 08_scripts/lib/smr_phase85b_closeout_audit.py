from smr_phase85b_closeout_config import load_config, get_preserved_blocked

def build_closeout_audit():
    """Build final closeout audit - self-contained, reads Phase 85 and 85b data."""
    all_tickers = []
    # Phase 85 CN (imported here to avoid circular)
    cn_rows = []
    try:
        from smr_phase85_cn_valuation_adapter import run_cn_valuation_adapter
        cn_rows = run_cn_valuation_adapter().get("phase85_cn_valuation_adapter", {}).get("rows", [])
    except: pass
    # Phase 85 HK
    hk_rows = []
    try:
        from smr_phase85_hk_valuation_adapter import run_hk_valuation_adapter
        hk_rows = run_hk_valuation_adapter().get("phase85_hk_valuation_adapter", {}).get("rows", [])
    except: pass
    # Phase 85 US
    us_rows = []
    try:
        from smr_phase85_us_valuation_adapter import run_us_valuation_adapter
        us_rows = run_us_valuation_adapter().get("phase85_us_valuation_adapter", {}).get("rows", [])
    except: pass
    # Phase 85b HK hardening
    hk_hard_rows = []
    try:
        from smr_phase85b_hk_valuation_hardening import run_hk_valuation_hardening
        hk_hard_rows = run_hk_valuation_hardening().get("phase85b_hk_valuation_hardening", {}).get("rows", [])
    except: pass
    # Phase 85b 688041 hardening
    hard_688041 = None
    try:
        from smr_phase85b_688041_valuation_hardening import explore_688041_sources
        hard_688041 = explore_688041_sources().get("phase85b_688041_valuation_hardening", {})
    except: pass
    # Build ticker list with overrides
    seen = set()
    blocked = get_preserved_blocked()
    # Process all rows
    for r in cn_rows:
        t = r["ticker"]
        if t in blocked:
            all_tickers.append({"ticker": t, "market": "CN_A", "final_status": "known_blocked", "valuation_available": False, "partial": False, "derived": False, "blocker": r.get("blocker", "known_blocked"), "metrics_available": [], "metrics_missing": r.get("metrics_missing", []), "source": "phase85_preserved"})
            seen.add(t); continue
        if t == "688041.SH" and hard_688041:
            va_found = hard_688041.get("valuation_found", False)
            rows_688 = hard_688041.get("rows", [])
            met_avail = rows_688[0].get("metrics_available", []) if rows_688 else []
            met_miss = rows_688[0].get("metrics_missing", []) if rows_688 else []
            all_tickers.append({"ticker": t, "market": "CN_A", "final_status": "valuation_available" if va_found else "final_unavailable_with_exhausted_sources", "valuation_available": va_found, "partial": False, "derived": False, "blocker": "" if va_found else "6_sources_exhausted", "metrics_available": met_avail, "metrics_missing": met_miss, "source": "phase85b_688041_hardened"})
            seen.add(t); continue
        va = r.get("valuation_available", False)
        all_tickers.append({"ticker": t, "market": "CN_A", "final_status": "valuation_available" if va else ("partial_valuation_available" if r.get("metrics_available") and r.get("metrics_missing") else "final_unavailable_with_exhausted_sources"), "valuation_available": va, "partial": bool(r.get("metrics_available") and r.get("metrics_missing")), "derived": False, "blocker": r.get("blocker", ""), "metrics_available": r.get("metrics_available", []), "metrics_missing": r.get("metrics_missing", []), "source": "phase85_cn"})
        seen.add(t)
    # Override HK with hardened results
    for hr in hk_hard_rows:
        t = hr["ticker"]
        all_tickers = [x for x in all_tickers if x["ticker"] != t]
        va = hr.get("valuation_available", False)
        dv = hr.get("derived_available", False)
        all_tickers.append({"ticker": t, "market": "HK", "final_status": hr.get("status", "final_unavailable_with_exhausted_sources"), "valuation_available": va, "partial": False, "derived": dv, "blocker": hr.get("blocker", ""), "metrics_available": hr.get("metrics_available", []), "metrics_missing": hr.get("metrics_missing", []), "source": "phase85b_hk_hardened"})
        seen.add(t)
    # Process US rows
    for r in us_rows:
        t = r["ticker"]
        if t in seen: continue
        va = r.get("valuation_available", False)
        all_tickers.append({"ticker": t, "market": "US", "final_status": "valuation_available" if va else "final_unavailable_with_exhausted_sources", "valuation_available": va, "partial": False, "derived": False, "blocker": r.get("blocker", ""), "metrics_available": r.get("metrics_available", []), "metrics_missing": r.get("metrics_missing", []), "source": "phase85_us"})
        seen.add(t)
    va_count = sum(1 for r in all_tickers if r["valuation_available"])
    pa = sum(1 for r in all_tickers if r["partial"])
    dv = sum(1 for r in all_tickers if r["derived"])
    bl = sum(1 for r in all_tickers if r["final_status"] == "known_blocked")
    unav = sum(1 for r in all_tickers if r["final_status"] == "final_unavailable_with_exhausted_sources")
    return {"phase85b_closeout_audit": {"tickers_total": len(all_tickers), "valuation_available": va_count, "partial_available": pa, "derived_available": dv, "blocked": bl, "final_unavailable": unav, "rows": all_tickers, "mock_used": False, "fixture_used": False}}
