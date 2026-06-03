def build_domain_registry():
 domains={
  "historical_blocker_loader":{"desc":"Load 300394 blocker history from Phase82-129","category":"input"},
  "identity_evidence_pack":{"desc":"Build 300394 identity evidence pack","category":"resolution"},
  "cninfo_candidate_registry":{"desc":"CNINFO org ID candidate registry for 300394","category":"resolution"},
  "cninfo_verification_runner":{"desc":"Verify CNINFO org ID candidates","category":"resolution"},
  "szse_disclosure_fallback":{"desc":"SZSE disclosure fallback for 300394","category":"alternative"},
  "irm_interaction_fallback":{"desc":"IRM interaction platform fallback","category":"alternative"},
  "company_ir_loader":{"desc":"Company IR website source loader","category":"alternative"},
  "known_url_validator":{"desc":"Validate known disclosure URLs for 300394","category":"resolution"},
  "manual_url_template":{"desc":"Manual URL seed template builder","category":"manual"},
  "alternative_disclosure_registry":{"desc":"Alternative disclosure source registry","category":"alternative"},
  "source_equivalence_scorer":{"desc":"Score alternative source equivalence","category":"pipeline"},
  "disclosure_coverage_classifier":{"desc":"Classify disclosure coverage level","category":"pipeline"},
  "hard_data_readiness_update":{"desc":"Update hard-data readiness for 300394","category":"pipeline"},
  "watchlist_status_update":{"desc":"Update watchlist status for 300394","category":"pipeline"},
  "gap_closeout_report":{"desc":"Gap closeout report builder","category":"output"},
  "manual_action_template":{"desc":"Manual action template for owner","category":"manual"},
  "resolution_decision_report":{"desc":"Blocker resolution decision report","category":"output"},
  "integration_update":{"desc":"Downstream integration update","category":"pipeline"},
  "resolution_board":{"desc":"Resolution board","category":"output"},
  "resolution_brief":{"desc":"Resolution brief","category":"output"},
  "resolution_memory":{"desc":"Resolution memory writer","category":"output"},
  "cannot_conclude_guard":{"desc":"Cannot-conclude guard","category":"safety"},
  "backlog_update":{"desc":"Backlog update","category":"output"}
 }
 return {"phase130_domain_registry":{"total":len(domains),"all_research_only":True,"domains":{k:{**v,"research_only":True} for k,v in domains.items()},"mock_used":False,"fixture_used":False}}
