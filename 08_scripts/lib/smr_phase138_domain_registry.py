def build_domain_registry():
 domains={
  "phase138_config":{"desc":"Phase138 config","category":"input"},
  "phase137_execution_loader":{"desc":"Load Phase137 execution","category":"input"},
  "research_context_loader":{"desc":"Load Phase112-137 research context","category":"input"},
  "ticker_thesis_schema":{"desc":"Ticker thesis schema","category":"core"},
  "thesis_entity_registry":{"desc":"Thesis entity registry","category":"core"},
  "evidence_to_thesis_linker":{"desc":"Link evidence to thesis","category":"core"},
  "finding_to_thesis_updater":{"desc":"Update thesis from findings","category":"execution"},
  "thesis_status_classifier":{"desc":"Classify thesis status","category":"analytics"},
  "thesis_confidence_scorer":{"desc":"Score thesis confidence","category":"analytics"},
  "contradiction_risk_linker":{"desc":"Link contradictions and risks","category":"analytics"},
  "thesis_change_log":{"desc":"Thesis change log","category":"output"},
  "research_memory_graph_builder":{"desc":"Build research memory graph","category":"output"},
  "ticker_thesis_card_builder":{"desc":"Build ticker thesis cards","category":"output"},
  "cross_ticker_theme_map":{"desc":"Cross-ticker theme map","category":"output"},
  "thesis_library_board":{"desc":"Thesis library board","category":"output"},
  "thesis_library_brief":{"desc":"Thesis library brief","category":"output"},
  "console_integration_update":{"desc":"Console integration","category":"output"},
  "daily_brief_integration_update":{"desc":"Daily brief integration","category":"output"},
  "decision_journal_integration_update":{"desc":"Decision journal integration","category":"output"},
  "thesis_memory_writer":{"desc":"Thesis memory writer","category":"output"},
  "quality_gate":{"desc":"Quality gate","category":"safety"},
  "cannot_conclude_guard":{"desc":"Cannot-conclude guard","category":"safety"},
  "backlog_update":{"desc":"Backlog update","category":"output"}
 }
 return {"phase138_domain_registry":{"total":len(domains),"all_research_only":True,"domains":{k:{**v,"research_only":True,"trade_action_allowed":False} for k,v in domains.items()},"mock_used":False,"fixture_used":False}}
