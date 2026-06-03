def build_domain_registry():
 domains={
  "phase130_resolution_loader":{"desc":"Load Phase130 resolution results","category":"input"},
  "alternative_source_registry_loader":{"desc":"Load alternative source registry from Phase130","category":"input"},
  "eastmoney_financial_adapter":{"desc":"Eastmoney financial data adapter for 300394","category":"adapter"},
  "szse_disclosure_metadata_adapter":{"desc":"SZSE disclosure metadata adapter","category":"adapter"},
  "irm_interaction_metadata_adapter":{"desc":"IRM interaction metadata adapter","category":"adapter"},
  "company_ir_metadata_adapter":{"desc":"Company IR metadata adapter","category":"adapter"},
  "known_url_integration_loader":{"desc":"Load known URLs into adapter config","category":"adapter"},
  "alternative_source_normalizer":{"desc":"Normalize alternative source data to standard schema","category":"pipeline"},
  "alternative_source_quality_gate":{"desc":"Quality gate for alternative source data","category":"pipeline"},
  "hard_data_integration_update":{"desc":"Update hard-data readiness after integration","category":"pipeline"},
  "watchlist_coverage_update":{"desc":"Update watchlist coverage with 300394","category":"pipeline"},
  "daily_brief_integration_update":{"desc":"Update daily brief with 300394","category":"pipeline"},
  "signal_effectiveness_update":{"desc":"Update signal effectiveness samples","category":"pipeline"},
  "health_gap_register_update":{"desc":"Update health and gap register","category":"pipeline"},
  "integration_decision_builder":{"desc":"Build integration decision report","category":"output"},
  "integration_board":{"desc":"Integration status board","category":"output"},
  "integration_brief":{"desc":"Integration brief","category":"output"},
  "integration_memory":{"desc":"Integration memory writer","category":"output"},
  "cannot_conclude_guard":{"desc":"Cannot-conclude guard","category":"safety"},
  "backlog_update":{"desc":"Backlog update","category":"output"}
 }
 return {"phase131_domain_registry":{"total":len(domains),"all_research_only":True,"domains":{k:{**v,"research_only":True} for k,v in domains.items()},"mock_used":False,"fixture_used":False}}
