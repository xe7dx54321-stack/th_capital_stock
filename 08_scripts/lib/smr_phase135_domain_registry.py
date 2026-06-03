def build_domain_registry():
 domains={
  "phase135_config":{"desc":"Phase135 config loader","category":"input"},
  "phase134_console_loader":{"desc":"Load Phase134 console export","category":"input"},
  "console_feedback_schema_builder":{"desc":"Build feedback schema","category":"core"},
  "ticker_card_feedback_intake":{"desc":"Ticker card feedback intake","category":"input"},
  "owner_action_feedback_intake":{"desc":"Owner action feedback intake","category":"input"},
  "daily_brief_feedback_intake":{"desc":"Daily brief feedback intake","category":"input"},
  "source_signal_feedback_intake":{"desc":"Source/signal feedback intake","category":"input"},
  "gap_risk_feedback_intake":{"desc":"Gap/risk feedback intake","category":"input"},
  "seasonal_insight_feedback_intake":{"desc":"Seasonal insight feedback intake","category":"input"},
  "feedback_validator":{"desc":"Validate feedback against rules","category":"safety"},
  "feedback_entity_linker":{"desc":"Link feedback to entities","category":"core"},
  "research_priority_feedback_adapter":{"desc":"Adapt feedback to research priority","category":"analytics"},
  "brief_layout_feedback_adapter":{"desc":"Adapt feedback to brief layout","category":"analytics"},
  "source_signal_weight_feedback_adapter":{"desc":"Adapt feedback to source/signal weight","category":"analytics"},
  "deep_dive_task_feedback_adapter":{"desc":"Adapt feedback to deep dive task","category":"analytics"},
  "research_loop_tuning_recommendation_builder":{"desc":"Build tuning recommendation","category":"output"},
  "feedback_impact_board_builder":{"desc":"Build feedback impact board","category":"output"},
  "feedback_integration_brief":{"desc":"Feedback integration brief","category":"output"},
  "console_feedback_template":{"desc":"Console feedback template","category":"output"},
  "feedback_integration_memory":{"desc":"Feedback memory writer","category":"output"},
  "cannot_conclude_guard":{"desc":"Cannot-conclude guard","category":"safety"},
  "backlog_update":{"desc":"Backlog update","category":"output"}
 }
 return {"phase135_domain_registry":{"total":len(domains),"all_research_only":True,"domains":{k:{**v,"research_only":True,"trade_action_allowed":False} for k,v in domains.items()},"mock_used":False,"fixture_used":False}}
