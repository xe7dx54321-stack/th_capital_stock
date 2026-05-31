def explore_688041_sources():
    results = []
    avail = []; miss = ["ev_revenue", "ev_ebitda"]; va = False; src = ""; all_attempted = []; errors = []
    # Source 1: akshare stock_individual_info_em
    all_attempted.append("akshare_stock_individual_info_em")
    try:
        import akshare as ak
        df = ak.stock_individual_info_em(symbol="688041")
        if df is not None and not df.empty:
            info = {row["item"]: row["value"] for _, row in df.iterrows() if "item" in row and "value" in row}
            mc = info.get("\u603b\u5e02\u503c") or info.get("\u5e02\u503c") or info.get("\u6d41\u901a\u5e02\u503c")
            pe = info.get("\u5e02\u76c8\u7387") or info.get("\u5e02\u76c8\u7387-\u52a8\u6001")
            pb = info.get("\u5e02\u51c0\u7387")
            ps = info.get("\u5e02\u9500\u7387")
            if mc: avail.append("market_cap")
            if pe: avail.append("pe_ttm")
            if pb: avail.append("pb")
            if ps: avail.append("ps_ttm")
            if avail: va = True; src = "akshare_stock_individual_info_em"
    except Exception as e:
        errors.append({"source": "akshare_stock_individual_info_em", "error": str(e)[:200]})
    # Source 2: yfinance 688041.SH
    if not va:
        all_attempted.append("yfinance_688041_SH")
        try:
            import yfinance as yf
            info = yf.Ticker("688041.SH").info or {}
            if info.get("marketCap"): avail.append("market_cap")
            if info.get("trailingPE"): avail.append("pe_ttm")
            if info.get("priceToSalesTrailing12Months"): avail.append("ps_ttm")
            if info.get("priceToBook"): avail.append("pb")
            if avail: va = True; src = "yfinance_688041_SH"
        except Exception as e:
            errors.append({"source": "yfinance_688041_SH", "error": str(e)[:200]})
    # Source 3: akshare stock_kc_a_spot_em
    if not va:
        all_attempted.append("akshare_stock_kc_a_spot_em")
        try:
            import akshare as ak
            df = ak.stock_kc_a_spot_em()
            row = df[df["\u4ee3\u7801"] == "688041"] if df is not None and "\u4ee3\u7801" in df.columns else None
            if row is not None and len(row) > 0:
                r = row.iloc[0]
                mc_val = r.get("\u603b\u5e02\u503c") or r.get("\u6d41\u901a\u5e02\u503c")
                if mc_val and float(mc_val) > 0: avail.append("market_cap"); va = True; src = "akshare_stock_kc_a_spot_em"
        except Exception as e:
            errors.append({"source": "akshare_stock_kc_a_spot_em", "error": str(e)[:200]})
    # Source 4: akshare stock_zh_a_spot_em
    if not va:
        all_attempted.append("akshare_stock_zh_a_spot_em")
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            row = df[df["\u4ee3\u7801"] == "688041"] if df is not None and "\u4ee3\u7801" in df.columns else None
            if row is not None and len(row) > 0:
                r = row.iloc[0]
                mc_val = r.get("\u603b\u5e02\u503c") or r.get("\u6d41\u901a\u5e02\u503c")
                if mc_val and float(mc_val) > 0: avail.append("market_cap"); va = True; src = "akshare_stock_zh_a_spot_em"
        except Exception as e:
            errors.append({"source": "akshare_stock_zh_a_spot_em", "error": str(e)[:200]})
    # Source 5: akshare stock_info_global_em
    if not va:
        all_attempted.append("akshare_stock_info_global_em")
        try:
            import akshare as ak
            df = ak.stock_info_global_em(symbol="688041")
            if df is not None and not df.empty:
                mc_val = df.iloc[0].get("\u603b\u5e02\u503c") if "\u603b\u5e02\u503c" in df.columns else None
                if mc_val and float(mc_val) > 0: avail.append("market_cap"); va = True; src = "akshare_stock_info_global_em"
        except Exception as e:
            errors.append({"source": "akshare_stock_info_global_em", "error": str(e)[:200]})
    # Source 6: akshare stock_individual_basic_info_xq
    if not va:
        all_attempted.append("akshare_stock_individual_basic_info_xq")
        try:
            import akshare as ak
            info = ak.stock_individual_basic_info_xq(symbol="SH688041")
            if info and isinstance(info, dict):
                mc_val = info.get("market_cap") or info.get("total_cap")
                if mc_val: avail.append("market_cap"); va = True; src = "akshare_stock_individual_basic_info_xq"
        except Exception as e:
            errors.append({"source": "akshare_stock_individual_basic_info_xq", "error": str(e)[:200]})
    if not va:
        miss = sorted(set(miss + ["market_cap", "pe_ttm", "ps_ttm", "pb"]))
    final_status = "valuation_available" if va else "final_unavailable_with_exhausted_sources"
    results.append({"ticker": "688041.SH", "market": "CN_A", "status": final_status, "blocker": "" if va else "all_6_sources_exhausted_for_688041", "valuation_available": va, "metrics_available": sorted(set(avail)), "metrics_missing": sorted(set(miss)), "sources_attempted": all_attempted, "source_success": src if va else "none", "source_errors": errors, "data_source": "real" if va else "exhausted", "mock_used": False, "fixture_used": False})
    return {"phase85b_688041_valuation_hardening": {"ticker": "688041.SH", "sources_attempted_count": len(all_attempted), "valuation_found": va, "final_status": final_status, "rows": results, "mock_used": False, "fixture_used": False}}
