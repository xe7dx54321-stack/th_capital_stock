def integrate_signals_valuation(daily_signals,band_results):
    bands_by_ticker={b["ticker"]:b for b in band_results}
    rows=[]
    for s in daily_signals:
        t=s["ticker"];band=bands_by_ticker.get(t,{"band":"unavailable","reason":"no_band_data"});valuation_note=""
        if s.get("delta_status")=="strengthened":
            if band["band"] in["low","neutral"]:valuation_note="signal_strengthened_valuation_reasonable"
            elif band["band"]=="high":valuation_note="signal_strengthened_valuation_elevated_watch_only"
            elif band["band"]=="stretched":valuation_note="signal_strengthened_valuation_stretched_watch_only"
            else:valuation_note="signal_strengthened_valuation_unavailable"
        elif s.get("delta_status")=="weakened":
            if band["band"]=="stretched":valuation_note="signal_weakened_valuation_stretched"
            else:valuation_note="signal_weakened"
        else:valuation_note="signal_unchanged"
        rows.append({"ticker":t,"market":s.get("market",""),"metric":s.get("metric_name",""),"delta_status":s.get("delta_status",""),"valuation_band":band["band"],"valuation_note":valuation_note,"cannot_conclude":s.get("cannot_conclude",[])})
    return {"phase85_valuation_daily_integration":{"integrated_signals":len(rows),"rows":rows,"mock_used":False,"fixture_used":False}}
