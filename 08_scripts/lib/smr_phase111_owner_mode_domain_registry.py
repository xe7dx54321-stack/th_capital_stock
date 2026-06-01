def build_owner_mode_domain_registry():
    domains={
        "research_support":{"description":"自动研究支持，财务数据分析与监控","active":True,"input_required":"watchlist_tickers","output":"research_packet_and_brief"},
        "opportunity_discovery":{"description":"机会发现与雷达","active":True,"input_required":"market_data_and_signals","output":"opportunity_radar"},
        "watchlist_tracking":{"description":"观察仓持续跟踪","active":True,"input_required":"covered_ticker_signals","output":"watch_board"},
        "owner_confirmation":{"description":"主人确认门控","active":True,"input_required":"action_candidate","output":"confirmed_or_rejected"},
        "research_journal":{"description":"研究日志与复盘","active":True,"input_required":"daily_run_history","output":"decision_journal"},
        "multi_user_assignment":{"description":"多用户身份指派","active":False,"reason":"personal_owner_mode_does_not_require_multi_user"},
        "paper_execution":{"description":"Paper执行系统","active":False,"reason":"paper_execution_permanently_disabled"},
        "live_trading":{"description":"真实交易","active":False,"reason":"live_trading_permanently_disabled"},
        "broker_integration":{"description":"券商集成","active":False,"reason":"broker_integration_not_allowed"},
        "position_sizing":{"description":"仓位计算","active":False,"reason":"position_sizing_disabled"},
        "target_price":{"description":"目标价","active":False,"reason":"target_price_disabled"},
        "pnl_tracking":{"description":"盈亏跟踪","active":False,"reason":"pnl_not_calculated"}
    }
    active_domains=sum(1 for d in domains.values() if d["active"])
    return {"phase111_owner_mode_domain_registry":{"total_domains":len(domains),"active_domains":active_domains,"deprecated_domains":len(domains)-active_domains,"domains":domains,"personal_use_system":True,"multi_user_system":False,"paper_execution_system":False,"mock_used":False,"fixture_used":False}}
