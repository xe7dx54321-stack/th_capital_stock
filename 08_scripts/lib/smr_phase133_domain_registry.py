def build_domain_registry():
 domains={
  "phase132_full_coverage_loader":{"desc":"Load Phase132 full coverage state","category":"input"},
  "seasonal_period_registry":{"desc":"Seasonal period definitions","category":"input"},
  "ticker_financial_valuation_loader":{"desc":"Load financial+valuation data for all 8 tickers","category":"input"},
  "ticker_seasonal_profile_builder":{"desc":"Build per-ticker seasonal profile","category":"analytics"},
  "cross_market_comparison_builder":{"desc":"Cross-market comparison panel","category":"analytics"},
  "financial_trend_panel_builder":{"desc":"Financial trend seasonal panel","category":"analytics"},
  "valuation_trend_panel_builder":{"desc":"Valuation trend seasonal panel","category":"analytics"},
  "opportunity_catalyst_panel_builder":{"desc":"Opportunity/catalyst seasonal panel","category":"analytics"},
  "watchlist_status_panel_builder":{"desc":"Watchlist seasonal status panel","category":"analytics"},
  "source_coverage_panel_builder":{"desc":"Source coverage seasonal panel","category":"analytics"},
  "signal_effectiveness_panel_builder":{"desc":"Signal effectiveness seasonal panel","category":"analytics"},
  "gap_risk_panel_builder":{"desc":"Gap/risk seasonal panel","category":"analytics"},
  "owner_action_queue_builder":{"desc":"Owner action seasonal queue","category":"analytics"},
  "seasonal_analytics_board":{"desc":"Seasonal analytics board","category":"output"},
  "seasonal_analytics_brief":{"desc":"Seasonal analytics brief","category":"output"},
  "seasonal_dashboard_exporter":{"desc":"Export seasonal dashboard","category":"output"},
  "seasonal_analytics_memory":{"desc":"Seasonal analytics memory writer","category":"output"},
  "cannot_conclude_guard":{"desc":"Cannot-conclude guard","category":"safety"},
  "backlog_update":{"desc":"Backlog update","category":"output"}
 }
 return {"phase133_domain_registry":{"total":len(domains),"all_research_only":True,"domains":{k:{**v,"research_only":True} for k,v in domains.items()},"mock_used":False,"fixture_used":False}}
