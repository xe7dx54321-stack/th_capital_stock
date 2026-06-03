def build_domain_registry():
 domains={
  "phase133_dashboard_loader":{"desc":"Load Phase133 seasonal analytics dashboard","category":"input"},
  "console_data_aggregator":{"desc":"Aggregate cross-phase console data","category":"core"},
  "ticker_card_builder":{"desc":"Build per-ticker research cards","category":"output"},
  "market_section_builder":{"desc":"Build CN_A/HK/US market sections","category":"output"},
  "research_priority_builder":{"desc":"Rank research priority","category":"analytics"},
  "seasonal_insight_center":{"desc":"Seasonal insight aggregation","category":"analytics"},
  "watchlist_status_center":{"desc":"Watchlist status center","category":"analytics"},
  "opportunity_catalyst_center":{"desc":"Opportunity and catalyst center","category":"analytics"},
  "source_signal_quality_center":{"desc":"Source and signal quality center","category":"analytics"},
  "gap_risk_center":{"desc":"Gap and risk center","category":"analytics"},
  "owner_action_center":{"desc":"Owner action center","category":"analytics"},
  "daily_brief_preview":{"desc":"Daily brief preview","category":"output"},
  "memory_feedback_center":{"desc":"Memory/feedback/decision center","category":"analytics"},
  "system_health_snapshot":{"desc":"System health snapshot","category":"output"},
  "artifact_link_index":{"desc":"Artifact link index","category":"output"},
  "console_quality_gate":{"desc":"Console quality gate","category":"safety"},
  "cannot_conclude_guard":{"desc":"Cannot-conclude guard","category":"safety"},
  "backlog_update":{"desc":"Backlog update","category":"output"},
  "console_memory":{"desc":"Console memory writer","category":"output"}
 }
 return {"phase134_domain_registry":{"total":len(domains),"all_research_only":True,"domains":{k:{**v,"research_only":True} for k,v in domains.items()},"mock_used":False,"fixture_used":False}}
