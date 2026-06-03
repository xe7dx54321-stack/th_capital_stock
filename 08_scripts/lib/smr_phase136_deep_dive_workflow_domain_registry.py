def build_domain_registry():
 domains={
  "phase136_config":{"desc":"Phase136 config loader","category":"input"},
  "phase135_feedback_task_loader":{"desc":"Load Phase135 feedback tasks","category":"input"},
  "deep_dive_task_schema":{"desc":"Deep dive task schema","category":"core"},
  "task_prioritizer":{"desc":"Prioritize deep dive tasks","category":"analytics"},
  "task_entity_linker":{"desc":"Link tasks to entities","category":"core"},
  "evidence_requirement_builder":{"desc":"Build evidence requirements","category":"analytics"},
  "source_plan_builder":{"desc":"Build source plans","category":"analytics"},
  "research_question_generator":{"desc":"Generate research questions","category":"analytics"},
  "execution_plan_builder":{"desc":"Build execution plan","category":"analytics"},
  "evidence_checklist":{"desc":"Build evidence checklist","category":"output"},
  "research_packet_builder":{"desc":"Build research packet","category":"output"},
  "deep_dive_brief_builder":{"desc":"Build deep dive brief","category":"output"},
  "task_status_tracker":{"desc":"Track task status","category":"output"},
  "console_integration_update":{"desc":"Update console with tasks","category":"output"},
  "daily_brief_integration_update":{"desc":"Update daily brief with tasks","category":"output"},
  "feedback_memory_integration_update":{"desc":"Update feedback memory","category":"output"},
  "decision_journal_candidate_update":{"desc":"Update decision journal","category":"output"},
  "deep_dive_quality_gate":{"desc":"Deep dive quality gate","category":"safety"},
  "cannot_conclude_guard":{"desc":"Cannot-conclude guard","category":"safety"},
  "backlog_update":{"desc":"Backlog update","category":"output"}
 }
 return {"phase136_deep_dive_workflow_domain_registry":{"total":len(domains),"all_research_only":True,"domains":{k:{**v,"research_only":True,"trade_action_allowed":False} for k,v in domains.items()},"mock_used":False,"fixture_used":False}}
