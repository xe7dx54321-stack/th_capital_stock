def classify_ticker(ticker_result):
    if ticker_result.get("coverage_status")=="blocked" or ticker_result.get("blocker"):return "blocked"
    if ticker_result.get("anomaly_count",0)>0:return "anomaly"
    if ticker_result.get("strengthened_count",0)>ticker_result.get("weakened_count",0):return "strengthened"
    if ticker_result.get("weakened_count",0)>ticker_result.get("strengthened_count",0):return "weakened"
    return "unchanged"
def build_classification(ticker_results):
    rows=[]
    for tr in ticker_results:
        cat=classify_ticker(tr);rows.append({"ticker":tr["ticker"],"market":tr["market"],"classification":cat,"strengthened_count":tr.get("strengthened_count",0),"weakened_count":tr.get("weakened_count",0),"unchanged_count":tr.get("unchanged_count",0),"anomaly_count":tr.get("anomaly_count",0),"blocked":cat=="blocked","blocker":tr.get("blocker","")})
    return {"phase84_daily_status_classifier":{"tickers_classified":len(rows),"strengthened":sum(1 for r in rows if r["classification"]=="strengthened"),"weakened":sum(1 for r in rows if r["classification"]=="weakened"),"unchanged":sum(1 for r in rows if r["classification"]=="unchanged"),"anomaly":sum(1 for r in rows if r["classification"]=="anomaly"),"blocked":sum(1 for r in rows if r["classification"]=="blocked"),"rows":rows,"mock_used":False,"fixture_used":False}}
