def build_domain_registry():
 domains={
  "phase139_config":{"desc":"Config","category":"input"},
  "phase138_thesis_loader":{"desc":"Load Phase138 thesis","category":"input"},
  "run_schedule_profile":{"desc":"Run schedule profile","category":"core"},
  "daily_research_run_plan":{"desc":"Daily run plan","category":"core"},
  "weekly_research_review_run_plan":{"desc":"Weekly review plan","category":"core"},
  "module_execution_planner":{"desc":"Module execution planner","category":"core"},
  "delivery_package_builder":{"desc":"Build delivery package","category":"output"},
  "owner_delivery_index":{"desc":"Owner delivery index","category":"output"},
  "local_notification_template":{"desc":"Local notification","category":"output"},
  "run_history_writer":{"desc":"Run history writer","category":"output"},
  "delivery_archive_writer":{"desc":"Archive writer","category":"output"},
  "failure_degraded_handling":{"desc":"Failure handling","category":"safety"},
  "delivery_quality_gate":{"desc":"Quality gate","category":"safety"},
  "cannot_conclude_guard":{"desc":"Cannot-conclude","category":"safety"},
  "backlog_update":{"desc":"Backlog","category":"output"}
 }
 return {"phase139_domain_registry":{"total":len(domains),"all_research_only":True,"domains":{k:{**v,"research_only":True,"trade_action_allowed":False} for k,v in domains.items()},"mock_used":False,"fixture_used":False}}
