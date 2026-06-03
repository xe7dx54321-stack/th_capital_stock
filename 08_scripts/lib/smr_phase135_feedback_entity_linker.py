def build_feedback_entity_linker():
 links=[
  {"feedback_id":"FB-TC-001","target_ticker":"NVDA","linked_entities":["NVDA_ticker_card","NVDA_seasonal_profile","NVDA_financial_signal"],"link_type":"ticker_card"},
  {"feedback_id":"FB-TC-002","target_ticker":"688041.SH","linked_entities":["688041_ticker_card","688041_valuation_gap","688041_seasonal_profile"],"link_type":"ticker_card"},
  {"feedback_id":"FB-OA-001","target_ticker":"688041.SH","linked_entities":["OA-134-002","688041_valuation_gap","688041_deep_dive_task"],"link_type":"owner_action"},
  {"feedback_id":"FB-DB-001","target_ticker":"ALL","linked_entities":["daily_brief_layout","seasonal_insight_center","brief_presentation"],"link_type":"daily_brief"},
  {"feedback_id":"FB-SS-001","target_ticker":"300394.SZ","linked_entities":["300394_source","eastmoney_source","signal_noise_filter"],"link_type":"source_signal"},
  {"feedback_id":"FB-SS-002","target_ticker":"NVDA","linked_entities":["NVDA_signal","NVDA_revenue_signal","signal_weight"],"link_type":"source_signal"},
  {"feedback_id":"FB-GR-001","target_ticker":"688041.SH","linked_entities":["688041_valuation_gap","research_priority_queue","gap_resolution_task"],"link_type":"gap_risk"},
  {"feedback_id":"FB-SI-001","target_ticker":"ALL","linked_entities":["seasonal_insight_center","seasonal_panels","brief_layout"],"link_type":"seasonal_insight"}
 ]
 return {"phase135_feedback_entity_linker":{"links":links,"total_linked":len(links),"mock_used":False,"fixture_used":False}}
