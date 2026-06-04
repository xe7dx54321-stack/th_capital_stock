def build_monitoring_signals(targets, mode="skip-network"):
    signals=[]
    for t in targets:
        tk=t["ticker"]
        signals.append({"ticker":tk,"signal_type":"hydration_status","signal_value":"deferred" if mode=="skip-network" else "live","monitoring_enabled":True,"signal_not_buy_sell_hold":True,"cannot_conclude":["signal_is_not_trade_recommendation","hydration_status_is_not_investment_opinion"]})
    return {"phase163_monitoring_signals":{"total":len(signals),"mode":mode,"signals":signals,"no_buy_sell_hold":True,"mock_used":False,"fixture_used":False}}

def build_daily_monitoring_adapter(signals, mode="skip-network"):
    integrated=[]
    for s in signals["phase163_monitoring_signals"]["signals"]:
        integrated.append({"ticker":s["ticker"],"daily_monitoring_status":"integrated_deferred" if mode=="skip-network" else "integrated_live","signal":s["signal_value"],"daily_monitoring_not_watch_update":True,"watch_core_updated":False})
    return {"phase163_daily_monitoring_adapter":{"total":len(integrated),"mode":mode,"integrated":integrated,"daily_monitoring_not_watch_update":True,"watch_core_updated":False,"mock_used":False,"fixture_used":False}}
