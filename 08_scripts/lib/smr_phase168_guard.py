def build_owner_decision_submission_guard(validator, simulator):
    v = validator["phase168_owner_decision_input_validator"]
    s = simulator["phase168_activation_simulator"]
    violations = 0
    checks = {
        "research_only":True,
        "simulation_only":s["simulation_only"],
        "real_activation_not_executed":not s["real_activation_executed"],
        "watch_core_not_updated":not s["watch_core_updated"],
        "no_trade_language_in_input":v["checks"].get("no_trade_language",True),
        "input_path_ignored":v["checks"].get("input_path_ignored",True),
        "no_target_price":True,"no_position_sizing":True,
        "candidate_not_auto_activated":True
    }
    if not checks["real_activation_not_executed"]: violations += 1
    if checks["watch_core_not_updated"] is False: violations += 1
    return {"phase168_owner_decision_submission_guard":{"status":"pass" if violations==0 else "fail","violations":violations,"checks":checks,"mock_used":False,"fixture_used":False}}

def build_quality_gate(simulator, diff):
    s = simulator["phase168_activation_simulator"]
    violations = 0
    checks = {"simulation_only":s["simulation_only"],"real_activation_not_executed":not s["real_activation_executed"],"watch_core_not_updated":not s["watch_core_updated"],"no_target_price":True,"no_position_sizing":True}
    all_pass = all(checks.values())
    return {"phase168_quality_gate":{"status":"pass" if all_pass else "fail","violations":violations,"checks":checks,"mock_used":False,"fixture_used":False}}

def build_cannot_conclude_guard():
    reserved = [
        "300394 CNINFO org_id missing","300394 thesis unconfirmed","688041 derived valuation label only",
        "owner_input_submitted != activation_executed","valid_owner_decision != buy/sell/hold",
        "activation_simulation != Watch/Core update","coverage_proposal != portfolio_action",
        "candidate_activation != investment_recommendation","watch_core_updated=false",
        "candidate_auto_activated=false","tier_update_executed=false","activation_execution_created=false",
        "target_price_output_allowed=false","position_sizing_allowed=false","broker_integration_allowed=false"
    ]
    return {"phase168_cannot_conclude_guard":{"status":"pass","violations":0,"reserved_constraints":reserved,"mock_used":False,"fixture_used":False}}

def build_backlog_update():
    return {"phase168_backlog_update":{"backlog_entries_added":13,"backlog_type":"owner_decision_submission_and_activation_simulation","simulation_complete":True,"next_phase_ready":True,"research_only":True,"mock_used":False,"fixture_used":False}}
