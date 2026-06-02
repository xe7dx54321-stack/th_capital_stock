def build_feedback_schema():
 s={"feedback_id":"string_uuid","created_at":"iso8601","feedback_type":"enum_12_types","target_entity":"ticker_or_candidate_or_source_or_gap_or_brief_section","feedback_text":"string","sentiment":"positive_or_neutral_or_negative","impact_level":"high_or_medium_or_low","owner_confidence":"certain_or_likely_or_uncertain","not_trade_instruction":"boolean_true_required","tags":"list_of_strings"}
 return {"phase123_feedback_schema":{"version":"v1","fields":list(s.keys()),"not_trade_mandatory":True,"research_only":True,"mock_used":False,"fixture_used":False}}
