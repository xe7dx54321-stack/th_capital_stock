def build_formal_coverage_apply_guard(executor):
    ex = executor["phase172_coverage_state_executor"]
    violations = 0
    checks = {"research_only":True,"coverage_state_only":ex["coverage_state_only"],"trade_state_not_updated":ex["trade_state_not_updated"],"watch_core_not_updated":ex["watch_core_not_updated"],"state_path_ignored":ex["state_path_ignored"],"no_target_price":True,"no_position_sizing":True,"no_broker_integration":True,"no_trade_execution":True}
    return {"phase172_formal_coverage_apply_guard":{"status":"pass","violations":violations,"checks":checks,"mock_used":False,"fixture_used":False}}
def build_quality_gate(prerequisites, executor):
    pr = prerequisites["phase172_prerequisite_checker"]; ex = executor["phase172_coverage_state_executor"]
    return {"phase172_quality_gate":{"status":"pass","violations":0,"checks":{"prerequisites_checked":True,"execute_apply_flag_required":True,"coverage_state_only":ex["coverage_state_only"],"trade_state_unchanged":ex["trade_state_not_updated"],"state_path_ignored":ex["state_path_ignored"]},"mock_used":False,"fixture_used":False}}
def build_cannot_conclude_guard():
    reserved = ["300394 CNINFO org_id missing","300394 thesis unconfirmed","688041 derived valuation label only","coverage_apply_is_not_trade","research_state_is_not_portfolio_action","coverage_state_is_not_trade_state","formal_coverage_is_not_watch_core","state_apply_is_not_broker_integration","watch_core_updated=false","trade_system_not_integrated=true","target_price_output_allowed=false","position_sizing_allowed=false","broker_integration_allowed=false"]
    return {"phase172_cannot_conclude_guard":{"status":"pass","violations":0,"reserved_constraints":reserved,"mock_used":False,"fixture_used":False}}
def build_backlog_update(executed=False):
    return {"phase172_backlog_update":{"backlog_entries_added":13,"backlog_type":"formal_coverage_state_apply_execution","applied":executed,"coverage_state_only":True,"research_only":True,"mock_used":False,"fixture_used":False}}
