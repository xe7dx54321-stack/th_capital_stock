def build_console_feedback_schema():
 schema={
  "feedback_types":["ticker_card_useful","ticker_card_not_useful","raise_research_attention","lower_research_attention","request_deep_dive","brief_too_long","brief_too_shallow","brief_priority_unclear","source_noisy","signal_helpful","gap_priority_high","gap_priority_low"],
  "feedback_record_schema":{
   "feedback_id":"string","created_at":"ISO8601","feedback_type":"enum","source_console_section":"enum","target_ticker":"string|null","target_entity_id":"string|null","owner_comment":"string","impact_scope":"enum","validation_status":"enum","research_only":True,"not_trade_feedback":True
  },
  "allowed_outputs":["increase_research_attention","decrease_research_attention","request_deep_dive","improve_brief_clarity","compress_low_value_section","expand_high_value_section","source_noise_flag","signal_usefulness_flag","gap_priority_adjustment","owner_preference_update"],
  "forbidden_outputs":["buy","sell","short","add_position","reduce_position","target_price","position_size","profit","loss","return","alpha","order","trade"],
  "empty_feedback_ready":True
 }
 return {"phase135_console_feedback_schema":{"schema":schema,"mock_used":False,"fixture_used":False}}
