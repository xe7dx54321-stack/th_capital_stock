def build_domain_registry():
 domains={
  "phase137_config":{"desc":"Phase137 config","category":"input"},
  "phase136_task_loader":{"desc":"Load Phase136 tasks","category":"input"},
  "task_execution_scope_resolver":{"desc":"Resolve execution scope","category":"core"},
  "existing_evidence_loader":{"desc":"Load existing evidence","category":"input"},
  "hard_data_evidence_updater":{"desc":"Update hard data evidence","category":"execution"},
  "valuation_evidence_updater":{"desc":"Update valuation evidence","category":"execution"},
  "source_evidence_updater":{"desc":"Update source evidence","category":"execution"},
  "catalyst_opportunity_evidence_updater":{"desc":"Update catalyst evidence","category":"execution"},
  "risk_gap_evidence_updater":{"desc":"Update risk/gap evidence","category":"execution"},
  "manual_confirmation_tracker":{"desc":"Track manual confirmations","category":"execution"},
  "task_finding_builder":{"desc":"Build task findings","category":"output"},
  "evidence_delta_classifier":{"desc":"Classify evidence deltas","category":"analytics"},
  "task_status_closeout_builder":{"desc":"Build task closeout","category":"output"},
  "updated_research_packet_builder":{"desc":"Build updated research packet","category":"output"},
  "deep_dive_execution_brief":{"desc":"Execution brief","category":"output"},
  "console_integration_update":{"desc":"Console update","category":"output"},
  "daily_brief_integration_update":{"desc":"Daily brief update","category":"output"},
  "feedback_memory_integration_update":{"desc":"Feedback memory update","category":"output"},
  "decision_journal_update_candidate":{"desc":"Decision journal update","category":"output"},
  "evidence_memory_writer":{"desc":"Evidence memory writer","category":"output"},
  "quality_gate":{"desc":"Quality gate","category":"safety"},
  "cannot_conclude_guard":{"desc":"Cannot-conclude guard","category":"safety"},
  "backlog_update":{"desc":"Backlog update","category":"output"}
 }
 return {"phase137_domain_registry":{"total":len(domains),"all_research_only":True,"domains":{k:{**v,"research_only":True,"trade_action_allowed":False} for k,v in domains.items()},"mock_used":False,"fixture_used":False}}
