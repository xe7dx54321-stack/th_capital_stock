def classify_band(ticker,metric_values,thresholds=None):
    if not thresholds:thresholds={"pe_ttm":{"low":15,"neutral":30,"high":50,"stretched":999},"ps_ttm":{"low":3,"neutral":8,"high":15,"stretched":999},"pb":{"low":1.5,"neutral":4,"high":8,"stretched":999}}
    pe=metric_values.get("pe_ttm");ps=metric_values.get("ps_ttm");pb=metric_values.get("pb")
    scores=[]
    for val,thr in[(pe,thresholds["pe_ttm"]),(ps,thresholds["ps_ttm"]),(pb,thresholds["pb"])]:
        if val is not None and isinstance(val,(int,float)):
            if val<=thr["low"]:scores.append("low")
            elif val<=thr["neutral"]:scores.append("neutral")
            elif val<=thr["high"]:scores.append("high")
            else:scores.append("stretched")
    if not scores:return "unavailable"
    if all(s=="low" for s in scores):return "low"
    if all(s=="high" for s in scores):return "high"
    if all(s=="stretched" for s in scores):return "stretched"
    from collections import Counter;c=Counter(scores);most=c.most_common(1)[0][0]
    return most
def classify_tickers(all_rows,thresholds=None):
    bands=[]
    for row in all_rows:
        if row.get("valuation_status")=="known_blocked" or row.get("status")=="known_blocked":bands.append({"ticker":row["ticker"],"band":"unavailable","reason":"known_blocked","pe_ttm":None,"ps_ttm":None,"pb":None});continue
        mv={"pe_ttm":row.get("pe_value"),"ps_ttm":row.get("ps_value"),"pb":row.get("pb_value")};band=classify_band(row["ticker"],mv,thresholds)
        bands.append({"ticker":row["ticker"],"band":band,"reason":"valuation_metrics_available" if band!="unavailable" else "metrics_missing","pe_ttm":row.get("pe_value"),"ps_ttm":row.get("ps_value"),"pb":row.get("pb_value")})
    band_mix={};from collections import Counter;c=Counter(b["band"] for b in bands);band_mix=dict(c)
    return {"phase85_valuation_band_classifier":{"bands_created":len(bands),"band_mix":band_mix,"rows":bands,"mock_used":False,"fixture_used":False}}
