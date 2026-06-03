def build_domain_registry():
 domains={
  "sec_edgar_fallback":{"desc":"SEC EDGAR fallback strategy","category":"official"},
  "hkex_fallback":{"desc":"HKEX fallback strategy","category":"official"},
  "transcript_fallback":{"desc":"Transcript guidance fallback strategy","category":"manual"},
  "mirror_registry":{"desc":"Official mirror source registry","category":"infra"},
  "third_party_equivalent":{"desc":"Third-party equivalent source registry","category":"infra"},
  "access_route_planner":{"desc":"Source access route planner","category":"pipeline"},
  "fallback_probe":{"desc":"Fallback probe executor","category":"pipeline"},
  "api_key_classifier":{"desc":"API-key required classifier","category":"pipeline"},
  "proxy_classifier":{"desc":"Proxy required classifier","category":"pipeline"},
  "manual_workflow":{"desc":"Manual source workflow builder","category":"pipeline"},
  "equivalence_scorer":{"desc":"Official source equivalence scorer","category":"pipeline"},
  "coverage_update":{"desc":"Fallback coverage update builder","category":"pipeline"},
  "gap_register":{"desc":"Official source gap register","category":"pipeline"},
  "integration_update":{"desc":"Downstream integration update","category":"pipeline"},
  "fallback_board":{"desc":"Official source fallback board","category":"output"},
  "fallback_brief":{"desc":"Official source fallback brief","category":"output"},
  "fallback_memory":{"desc":"Fallback memory writer","category":"output"},
  "cannot_conclude_guard":{"desc":"Cannot-conclude guard","category":"safety"},
  "backlog_update":{"desc":"Backlog update","category":"output"}
 }
 return {"phase129_domain_registry":{"total":len(domains),"all_research_only":True,"domains":{k:{**v,"research_only":True} for k,v in domains.items()},"mock_used":False,"fixture_used":False}}
