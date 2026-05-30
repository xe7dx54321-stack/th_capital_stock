def build(classifications):
    rows=[]
    for c in classifications:
        et="daily_"+c["classification"]+"_observed" if c["classification"]=="blocked" else "daily_"+c["classification"]+"_observed"
        rows.append({"ticker":c["ticker"],"evidence_type":et,"claim_type":"watch_status_"+c["classification"],"limitation":"每日监控状态不等于交易建议，不确认客户份额或订单。","cannot_conclude":["buy_signal","customer_share","confirmed"] if c["classification"]!="blocked" else ["buy_signal","coverage_missing"]})
    return {"phase84_daily_monitoring_evidence":{"tickers_checked":len(rows),"daily_evidence_created":len(rows),"rows":rows,"mock_used":False,"fixture_used":False}}
