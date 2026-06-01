def build_research_action_taxonomy():
    actions={
        "financial_monitoring":{"description":"财务数据持续监控","allows_order":False,"requires_owner_confirmation":False,"risk_level":"low"},
        "signal_tracking":{"description":"信号跟踪（strengthened/weakened/unchanged/anomaly）","allows_order":False,"requires_owner_confirmation":False,"risk_level":"low"},
        "watch_board_update":{"description":"观察仓看板更新","allows_order":False,"requires_owner_confirmation":False,"risk_level":"low"},
        "coverage_blocker_resolution":{"description":"覆盖障碍解决","allows_order":False,"requires_owner_confirmation":False,"risk_level":"low"},
        "evidence_memory_write":{"description":"证据记忆写入","allows_order":False,"requires_owner_confirmation":False,"risk_level":"low"},
        "research_brief_generation":{"description":"研报生成","allows_order":False,"requires_owner_confirmation":False,"risk_level":"low"},
        "opportunity_discovery":{"description":"机会发现","allows_order":False,"requires_owner_confirmation":True,"risk_level":"medium"},
        "valuation_analysis":{"description":"估值分析","allows_order":False,"requires_owner_confirmation":True,"risk_level":"medium"},
        "thesis_update":{"description":"投资论文更新","allows_order":False,"requires_owner_confirmation":True,"risk_level":"medium"},
        "paper_order_creation":{"description":"Paper下单","allows_order":True,"requires_owner_confirmation":False,"risk_level":"n/a","reason":"permanently_disabled","active":False},
        "live_trade_creation":{"description":"真实交易","allows_order":True,"requires_owner_confirmation":False,"risk_level":"n/a","reason":"permanently_disabled","active":False},
        "position_sizing":{"description":"仓位计算","allows_order":False,"requires_owner_confirmation":False,"risk_level":"n/a","reason":"permanently_disabled","active":False}
    }
    active_actions={k:v for k,v in actions.items() if v.get("active",True)==True}
    return {"phase111_research_action_taxonomy":{"total_actions":len(actions),"active_actions":len(active_actions),"disabled_actions":len(actions)-len(active_actions),"actions":actions,"no_order_actions":True,"research_only_mode":True,"mock_used":False,"fixture_used":False}}
