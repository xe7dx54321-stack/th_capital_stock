def build_domain_registry():
 domains={
  "phase131_coverage_loader":{"desc":"Load Phase131 coverage state","category":"input"},
  "historical_valuation_gap_loader":{"desc":"Load 688041 valuation gap history","category":"input"},
  "valuation_source_registry":{"desc":"Registry of valuation data sources","category":"input"},
  "eastmoney_valuation_adapter":{"desc":"Eastmoney valuation adapter for 688041","category":"adapter"},
  "akshare_star_valuation_adapter":{"desc":"Akshare STAR valuation adapter","category":"adapter"},
  "third_party_valuation_fallback":{"desc":"Third-party valuation fallback","category":"adapter"},
  "financial_metric_dependency_resolver":{"desc":"Resolve metrics needed for valuation calculation","category":"pipeline"},
  "ev_ebitda_input_builder":{"desc":"Build EV/EBITDA input data","category":"pipeline"},
  "ps_ratio_input_builder":{"desc":"Build PS ratio input data","category":"pipeline"},
  "alternative_valuation_metric_builder":{"desc":"Build alternative valuation metrics","category":"pipeline"},
  "valuation_source_normalizer":{"desc":"Normalize valuation data","category":"pipeline"},
  "valuation_quality_gate":{"desc":"Quality gate for valuation data","category":"pipeline"},
  "valuation_coverage_classifier":{"desc":"Classify valuation coverage level","category":"pipeline"},
  "hard_data_valuation_update":{"desc":"Update hard-data valuation readiness","category":"pipeline"},
  "watchlist_valuation_update":{"desc":"Update watchlist with valuation status","category":"pipeline"},
  "daily_brief_valuation_update":{"desc":"Update daily brief with valuation","category":"pipeline"},
  "signal_effectiveness_valuation_update":{"desc":"Update signal effectiveness","category":"pipeline"},
  "gap_closeout_report":{"desc":"Gap closeout report","category":"output"},
  "valuation_integration_board":{"desc":"Valuation integration board","category":"output"},
  "valuation_integration_brief":{"desc":"Valuation integration brief","category":"output"},
  "valuation_memory":{"desc":"Valuation memory writer","category":"output"},
  "cannot_conclude_guard":{"desc":"Cannot-conclude guard","category":"safety"},
  "backlog_update":{"desc":"Backlog update","category":"output"}
 }
 return {"phase132_domain_registry":{"total":len(domains),"all_research_only":True,"domains":{k:{**v,"research_only":True} for k,v in domains.items()},"mock_used":False,"fixture_used":False}}
