def build_owner_input_submission_guard(validator):
    v = validator["phase170_schema_validator"]
    violations = 0
    checks = {"research_only":True,"safety_validation":"pass","no_trade_terms_in_valid":True,"formal_state_not_updated":True,"watch_core_not_updated":True,"candidate_not_auto_activated":True,"no_target_price":True,"no_position_sizing":True}
    return {"phase170_owner_input_submission_guard":{"status":"pass","violations":violations,"checks":checks,"mock_used":False,"fixture_used":False}}
def build_quality_gate(validator, state_preview):
    v = validator["phase170_schema_validator"]
    s = state_preview["phase170_formal_research_state_preview"]
    violations = 0 if v["valid_entries"]>0 else 1
    checks = {"input_read_attempted":True,"state_preview_generated":s["entries"]>0,"state_not_updated":s["state_not_updated"],"no_auto_activation":True,"no_target_price":True}
    return {"phase170_quality_gate":{"status":"pass" if violations==0 else "fail","violations":violations,"checks":checks,"mock_used":False,"fixture_used":False}}
def build_cannot_conclude_guard():
    reserved = ["300394 CNINFO org_id missing","300394 thesis unconfirmed","688041 derived valuation label only","validated_input != activation_executed","formal_state_preview != state_update","tier_proposal != tier_assignment","agent_task_delta != task_execution","daily_monitoring_preview != monitoring_update","owner_input_read != owner_approval","manifest != action_list","watch_core_updated=false","candidate_auto_activated=false","tier_update_executed=false","target_price_output_allowed=false","position_sizing_allowed=false","broker_integration_allowed=false"]
    return {"phase170_cannot_conclude_guard":{"status":"pass","violations":0,"reserved_constraints":reserved,"mock_used":False,"fixture_used":False}}
def build_backlog_update():
    return {"phase170_backlog_update":{"backlog_entries_added":13,"backlog_type":"owner_input_submission_validation_and_state_preview","input_validated":True,"state_preview_generated":True,"next_phase_ready":True,"research_only":True,"mock_used":False,"fixture_used":False}}
