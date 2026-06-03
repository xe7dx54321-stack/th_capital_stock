def build_domain_registry():
 domains={
  "phase140_config":{"desc":"Config","category":"input"},
  "phase139_delivery_loader":{"desc":"Load Phase139 delivery","category":"input"},
  "module_regression_matrix":{"desc":"Regression matrix","category":"core"},
  "artifact_integrity_checker":{"desc":"Artifact check","category":"audit"},
  "config_consistency_auditor":{"desc":"Config audit","category":"audit"},
  "generated_path_auditor":{"desc":"Path/gitignore audit","category":"audit"},
  "safety_boundary_auditor":{"desc":"Safety audit","category":"audit"},
  "degradation_policy_validator":{"desc":"Degradation validator","category":"audit"},
  "run_history_consistency_checker":{"desc":"History check","category":"audit"},
  "delivery_package_integrity_checker":{"desc":"Package integrity","category":"audit"},
  "link_checker":{"desc":"Link checker","category":"audit"},
  "source_limitation_visibility_checker":{"desc":"Source limitation","category":"audit"},
  "known_blocker_retention_checker":{"desc":"Blocker retention","category":"audit"},
  "recovery_recommendation_builder":{"desc":"Recovery builder","category":"output"},
  "maintenance_checklist_builder":{"desc":"Maintenance checklist","category":"output"},
  "operational_reliability_scorecard":{"desc":"Scorecard","category":"output"},
  "hardening_board":{"desc":"Hardening board","category":"output"},
  "hardening_brief":{"desc":"Hardening brief","category":"output"},
  "reliability_memory_writer":{"desc":"Memory writer","category":"output"},
  "quality_gate":{"desc":"Quality gate","category":"safety"},
  "cannot_conclude_guard":{"desc":"Guard","category":"safety"},
  "backlog_update":{"desc":"Backlog","category":"output"}
 }
 return {"phase140_domain_registry":{"total":len(domains),"all_research_only":True,"domains":{k:{**v,"research_only":True} for k,v in domains.items()},"mock_used":False,"fixture_used":False}}
