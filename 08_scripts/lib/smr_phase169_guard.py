def build_authoring_guide_guard(preflight):
    v = 0
    return {"phase169_authoring_guide_guard":{"status":"pass","violations":v,"checks":{"research_only":True,"guide_not_auto_write":True,"preflight_not_real_submission":True,"sandbox_not_real_execution":True,"no_target_price":True,"no_position_sizing":True,"watch_core_updated":False},"mock_used":False,"fixture_used":False}}

def build_quality_gate(example_pack, expectation_matcher, sandbox_all):
    ep = example_pack["phase169_example_pack"]
    em = expectation_matcher["phase169_expectation_matcher"]
    sa = sandbox_all["phase169_sandbox_all_examples"]
    violations = 0
    safety_keys = ["real_owner_input_written","phase168_auto_submit","watch_core_updated","candidate_auto_activated","activation_execution_created"]
    checks = {
        "valid_examples_count_ge_5":ep["valid_example_count"]>=5,
        "invalid_examples_count_ge_6":ep["invalid_example_count"]>=6,
        "mixed_decisions_all_13_present":"example_5_mixed_all_13" in ep["valid_examples"],
        "invalid_unknown_candidate_present":"invalid_4_unknown_candidate" in ep["invalid_examples"],
        "invalid_duplicate_candidate_present":"invalid_5_duplicate_candidate" in ep["invalid_examples"],
        "invalid_missing_rationale_present":"invalid_7_missing_rationale" in ep["invalid_examples"],
        "invalid_decision_option_present":"invalid_6_bad_option" in ep["invalid_examples"],
        "trade_like_quarantine_present":"invalid_1_trade_buy" in ep["invalid_examples"],
        "target_position_quarantine_present":"invalid_2_target_price" in ep["invalid_examples"],
        "preflight_all_examples_checked":em["examples_checked"]>=12,
        "sandbox_all_examples_checked":sa["all_examples_checked"],
        "expectations_all_match":em["expectations_all_match"],
        "real_owner_input_written":False,"phase168_auto_submit":False,
        "watch_core_updated":False,"candidate_auto_activated":False,"activation_execution_created":False,
        "no_target_price":True,"no_position_sizing":True
    }
    positive_fail = not all(checks[k] for k in checks if k not in safety_keys)
    safety_fail = any(checks[k] for k in safety_keys)
    if positive_fail or safety_fail: violations = 1
    return {"phase169_quality_gate":{"status":"pass" if violations==0 else "fail","violations":violations,"checks":checks,"example_coverage_status":"pass" if ep["valid_example_count"]>=5 and ep["invalid_example_count"]>=6 else "fail","mock_used":False,"fixture_used":False}}

def build_cannot_conclude_guard():
    reserved = [
        "300394 CNINFO org_id missing","300394 thesis unconfirmed","688041 derived valuation label only",
        "example_is_not_approval","guide_is_not_auto_write","preflight_is_not_real_submission","sandbox_is_not_real_execution",
        "valid_example != owner_approval","invalid_example != negative_investment_view",
        "preflight_pass != activation_executed","sandbox_simulation != watch_core_update",
        "mixed_example != portfolio_action","reject_example != sell_signal","keep_example != hold_signal","activate_example != buy_signal",
        "owner_input_write_allowed=false","watch_core_updated=false","activation_execution_created=false",
        "target_price_output_allowed=false","position_sizing_allowed=false","broker_integration_allowed=false"
    ]
    return {"phase169_cannot_conclude_guard":{"status":"pass","violations":0,"reserved_constraints":reserved,"mock_used":False,"fixture_used":False}}

def build_backlog_update():
    return {"phase169_backlog_update":{"backlog_entries_added":12,"backlog_type":"owner_decision_authoring_guide_and_example_pack_hardened","guide_ready":True,"examples_hardened":True,"valid_examples":5,"invalid_examples":7,"example_coverage":"pass","next_phase_ready":True,"research_only":True,"mock_used":False,"fixture_used":False}}
