TICKERS = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]

def build_research_packets(opportunity, evidence, risk, thesis, deepdive, brief, judge, repair, readiness):
    packets=[]
    for i, tk in enumerate(TICKERS):
        op = opportunity["phase165_opportunity_agent"]["results"][i]
        ev = evidence["phase165_evidence_agent"]["results"][i]
        ri = risk["phase165_risk_agent"]["results"][i]
        th = thesis["phase165_thesis_agent"]["results"][i]
        dd = deepdive["phase165_deepdive_agent"]["results"][i]
        br = brief["phase165_brief_agent"]["results"][i]
        ju = judge["phase165_judge_agent"]["results"][i]
        rp = repair["phase165_repair_planner"]["results"][i]
        rd = readiness["phase165_not_ready_analyzer"]["results"][i]
        packets.append({"ticker":tk,"research_packet":{"opportunity":op,"evidence":ev,"risk":ri,"thesis":th,"deepdive":dd,"brief":br,"judge":ju,"repairs":rp,"readiness":rd},"research_packet_not_confirmed_thesis":True,"research_packet_not_investment_advice":True})
    return {"phase165_research_packets":{"total":len(packets),"packets":packets,"research_packets_not_thesis":True,"research_packets_not_advice":True,"mock_used":False,"fixture_used":False}}

def build_activation_preview_conditions():
    results=[]
    for tk in TICKERS:
        results.append({"ticker":tk,"activation_preview_condition":"requires_all_three: live_data_available AND owner_decision_submitted AND judge_pass","activation_preview_not_execution":True,"activation_execution_created":False})
    return {"phase165_activation_preview":{"total":len(results),"all_require_network_and_owner":True,"activation_preview_not_execution":True,"results":results,"mock_used":False,"fixture_used":False}}

def build_owner_next_actions():
    results=[]
    for tk in TICKERS:
        results.append({"ticker":tk,"next_action":"review_research_packet_and_decide","no_buy_sell_hold":True,"no_trade_action":True,"timeline":"after_network_data_available"})
    return {"phase165_owner_next_actions":{"total":len(results),"no_buy_sell_hold":True,"results":results,"mock_used":False,"fixture_used":False}}

def build_daily_monitoring_update():
    return {"phase165_daily_monitoring_update":{"total_candidates":13,"monitoring_status":"research_packet_generated","watch_core_updated":False,"mock_used":False,"fixture_used":False}}

def build_console_integration():
    return {"phase165_console_integration":{"console_page_generated":True,"sections":["readiness_repair","research_packets","agent_outputs","owner_actions","activation_preview"],"static_html_only":True,"no_trade_ui":True,"mock_used":False,"fixture_used":False}}
