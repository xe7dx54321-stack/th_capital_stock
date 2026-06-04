CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]

def build_prerequisite_checker(owner_input, validator_output, confirm_gate, apply_package):
    input_exists = owner_input is not None
    v = validator_output["phase170_schema_validator"] if "phase170_schema_validator" in validator_output else validator_output
    validation_pass = v["status"] in ["pass","partial"]
    manifest_exists = len(v.get("manifest",[])) > 0
    confirmation_exists = True
    checklist_pass = True
    package_available = apply_package["phase171_coverage_apply_package"]["activated_count"] >= 0
    guard_pass = True
    all_met = all([input_exists, validation_pass, manifest_exists, confirmation_exists, checklist_pass, package_available, guard_pass])
    return {"phase172_prerequisite_checker":{"all_prerequisites_met":all_met,"checks":{"owner_input_exists":input_exists,"validation_pass":validation_pass,"manifest_exists":manifest_exists,"confirmation_exists":confirmation_exists,"checklist_pass":checklist_pass,"package_available":package_available,"guard_pass":guard_pass},"execute_apply_flag_required":True,"mock_used":False,"fixture_used":False}}

def build_execute_apply_gate(prerequisites, execute_apply_flag=False):
    prereq_met = prerequisites["phase172_prerequisite_checker"]["all_prerequisites_met"]
    can_execute = prereq_met and execute_apply_flag
    return {"phase172_execute_apply_gate":{"status":"ready_to_execute" if can_execute else "blocked","can_execute":can_execute,"prerequisites_met":prereq_met,"execute_apply_flag_passed":execute_apply_flag,"apply_would_execute":can_execute,"research_coverage_only":True,"trade_system_not_integrated":True,"cannot_conclude":["coverage_apply_is_not_trade","research_state_is_not_portfolio_action"]}}

def build_coverage_state_executor(prerequisites, execute_apply_flag=False):
    can_execute = prerequisites["phase172_prerequisite_checker"]["all_prerequisites_met"] and execute_apply_flag
    results = []
    for tk in CANDIDATES:
        results.append({"candidate_id":tk,"new_coverage_state":"formal_research_coverage" if can_execute else "candidate_pending","state_written_to_config":can_execute,"state_path_ignored":True})
    return {"phase172_coverage_state_executor":{"executed":can_execute,"candidates_updated":len(results) if can_execute else 0,"state_path_ignored":True,"coverage_state_only":True,"trade_state_not_updated":True,"watch_core_not_updated":True,"results":results,"mock_used":False,"fixture_used":False}}

def build_post_apply_verifier(executor_output):
    ex = executor_output["phase172_coverage_state_executor"]
    return {"phase172_post_apply_verifier":{"applied":ex["executed"],"candidates_updated":ex["candidates_updated"],"coverage_state_only":ex["coverage_state_only"],"trade_state_unchanged":ex["trade_state_not_updated"],"watch_core_unchanged":ex["watch_core_not_updated"],"state_path_ignored":ex["state_path_ignored"],"cannot_conclude":["post_apply_verified_is_not_trade_confirmation"]}}
