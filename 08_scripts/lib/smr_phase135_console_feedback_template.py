def build_console_feedback_template():
 template={
  "template_name":"console_feedback_form",
  "sections":[
   {"section":"ticker_cards","feedback_types":["ticker_card_useful","ticker_card_not_useful","raise_research_attention","lower_research_attention","request_deep_dive"],"target":"ticker"},
   {"section":"daily_brief","feedback_types":["brief_too_long","brief_too_shallow","brief_priority_unclear"],"target":"brief_layout"},
   {"section":"source_signal","feedback_types":["source_noisy","signal_helpful"],"target":"source_or_signal"},
   {"section":"gap_risk","feedback_types":["gap_priority_high","gap_priority_low"],"target":"gap_or_risk_item"},
   {"section":"seasonal_insight","feedback_types":["ticker_card_useful","ticker_card_not_useful"],"target":"seasonal_panel"},
   {"section":"owner_action","feedback_types":["request_deep_dive"],"target":"owner_action_item"}
  ],
  "all_feedback_is_research_only":True,
  "no_trade_feedback_allowed":True,
  "forbidden_in_feedback":["buy","sell","short","target_price","position_size","profit","loss","return","alpha","order","trade"]
 }
 return {"phase135_console_feedback_template":{"template":template,"ready_for_owner_use":True,"mock_used":False,"fixture_used":False}}
