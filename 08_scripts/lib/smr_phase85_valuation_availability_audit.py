def build_availability_audit(cn_results,hk_results,us_results):
    all_rows=[]
    for r in cn_results+hk_results+us_results:
        status=r.get("status","");blocker=r.get("blocker","")
        if status=="known_blocked":all_rows.append({"ticker":r["ticker"],"market":r["market"],"valuation_status":"known_blocked","blocker":blocker,"valuation_available":False,"metrics_available":[],"metrics_missing":r.get("metrics_missing",[])})
        elif status=="available":all_rows.append({"ticker":r["ticker"],"market":r["market"],"valuation_status":"available" if not r.get("metrics_missing") else "partial","blocker":"","valuation_available":True,"metrics_available":r.get("metrics_available",[]),"metrics_missing":r.get("metrics_missing",[])})
        else:all_rows.append({"ticker":r["ticker"],"market":r["market"],"valuation_status":"unavailable","blocker":blocker or "valuation_source_failed","valuation_available":False,"metrics_available":[],"metrics_missing":r.get("metrics_missing",[])})
    va=sum(1 for r in all_rows if r["valuation_status"]=="available");pa=sum(1 for r in all_rows if r["valuation_status"]=="partial");ua=sum(1 for r in all_rows if r["valuation_status"]=="unavailable");kb=sum(1 for r in all_rows if r["valuation_status"]=="known_blocked")
    return {"phase85_valuation_availability_audit":{"tickers_checked":len(all_rows),"valuation_available":va,"partial":pa,"unavailable":ua,"known_blocked":kb,"rows":all_rows,"mock_used":False,"fixture_used":False}}
