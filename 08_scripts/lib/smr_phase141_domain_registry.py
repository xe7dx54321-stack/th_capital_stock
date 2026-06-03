def build_domain_registry():
 domains={
  "phase141_config":{"desc":"Config loader","category":"input"},
  "phase140_hardening_loader":{"desc":"Load Phase140 status","category":"input"},
  "phase139_delivery_loader":{"desc":"Load Phase139 delivery","category":"input"},
  "phase138_thesis_loader":{"desc":"Load Phase138 thesis","category":"input"},
  "phase134_console_loader":{"desc":"Load Phase134 console","category":"input"},
  "dashboard_data_model":{"desc":"Dashboard data model","category":"core"},
  "static_html_layout_builder":{"desc":"HTML layout","category":"output"},
  "css_style_builder":{"desc":"CSS styles","category":"output"},
  "navigation_anchor_system":{"desc":"Navigation","category":"output"},
  "ticker_card_html_section":{"desc":"Ticker cards HTML","category":"output"},
  "thesis_library_html_section":{"desc":"Thesis HTML","category":"output"},
  "evidence_source_limitation_html_section":{"desc":"Evidence HTML","category":"output"},
  "daily_weekly_delivery_html_section":{"desc":"Delivery HTML","category":"output"},
  "owner_action_html_section":{"desc":"Actions HTML","category":"output"},
  "gap_risk_html_section":{"desc":"Gap/Risk HTML","category":"output"},
  "feedback_template_html_section":{"desc":"Feedback HTML","category":"output"},
  "artifact_link_html_section":{"desc":"Links HTML","category":"output"},
  "local_open_instruction_builder":{"desc":"Open instructions","category":"output"},
  "html_quality_gate":{"desc":"Quality gate","category":"safety"},
  "cannot_conclude_guard":{"desc":"Guard","category":"safety"},
  "backlog_update":{"desc":"Backlog","category":"output"}
 }
 return {"phase141_domain_registry":{"total":len(domains),"all_research_only":True,"domains":{k:{**v,"research_only":True} for k,v in domains.items()},"mock_used":False,"fixture_used":False}}
