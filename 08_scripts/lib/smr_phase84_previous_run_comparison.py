import json
from smr_phase84_daily_run_history import load_history
def compare(current_run):
    runs=load_history()
    if not runs:return {"has_previous_run":False,"comparison_status":"first_run_baseline","reason":"no_prior_phase84_run_history","rows":[],"mock_used":False,"fixture_used":False}
    prev=runs[-1];prev_results={r["ticker"]:r for r in prev.get("ticker_results",[])}
    cur_results={r["ticker"]:r for r in current_run.get("ticker_results",[])}
    rows=[]
    for ticker,cr in cur_results.items():
        pr=prev_results.get(ticker)
        if pr:
            cs="status_unchanged"
            if cr.get("anomaly_count",0)>0 and pr.get("anomaly_count",0)==0:cs="new_anomaly"
            elif cr.get("strengthened_count",0)>pr.get("strengthened_count",0):cs="status_strengthened"
            elif cr.get("weakened_count",0)>pr.get("weakened_count",0):cs="status_weakened"
            rows.append({"ticker":ticker,"previous_status":pr.get("run_status","ok"),"current_status":cr.get("run_status","ok"),"comparison_status":cs,"reason":f"signal_delta_changed"})
        else:rows.append({"ticker":ticker,"comparison_status":"first_observation","reason":"newly_covered"})
    return {"phase84_previous_run_comparison":{"has_previous_run":True,"comparison_status":"compared","tickers_compared":len(rows),"status_strengthened":sum(1 for r in rows if r["comparison_status"]=="status_strengthened"),"status_weakened":sum(1 for r in rows if r["comparison_status"]=="status_weakened"),"new_anomaly":sum(1 for r in rows if r["comparison_status"]=="new_anomaly"),"newly_blocked":0,"rows":rows,"mock_used":False,"fixture_used":False}}
