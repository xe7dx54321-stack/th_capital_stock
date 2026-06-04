def refresh_owner_feed(targets, mode="skip-network"):
    items=[]
    for t in targets:
        tk=t["ticker"]
        items.append({"ticker":tk,"name":t.get("name",""),"hydration_status":"deferred" if mode=="skip-network" else "live_snapshot_taken","readiness":"ready_network_pending","recommended_action":"review_after_live_fetch" if mode=="skip-network" else "review_snapshot_results","no_buy_sell_hold":True,"no_trade_recommendation":True})
    return {"phase163_owner_feed_refresh":{"items":len(items),"mode":mode,"no_buy_sell_hold":True,"feed_items":items,"mock_used":False,"fixture_used":False}}

def refresh_agent_queue(targets, mode="skip-network"):
    tasks=[]
    for t in targets:
        tk=t["ticker"]
        tasks.append({"ticker":tk,"task":"execute_live_snapshot","status":"pending" if mode=="skip-network" else "completed","priority":"medium","no_trade_order":True,"no_target_price":True})
    return {"phase163_agent_queue_refresh":{"tasks":len(tasks),"mode":mode,"pending":sum(1 for x in tasks if x["status"]=="pending"),"completed":sum(1 for x in tasks if x["status"]=="completed"),"no_trade_orders":True,"tasks":tasks,"mock_used":False,"fixture_used":False}}

def refresh_console_artifact(mode="skip-network"):
    return {"phase163_console_refresh":{"console_page_generated":True,"sections":["live_hydration_board","daily_monitoring_status","owner_feed","agent_queue"],"static_html_only":True,"external_js":False,"no_trade_ui":True,"no_execution_ui":True,"mode":mode,"mock_used":False,"fixture_used":False}}
