CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]

def build_apply_confirmation_gate(validator_output):
    v = validator_output["phase170_schema_validator"] if "phase170_schema_validator" in validator_output else validator_output
    ready = v["status"] == "pass" or v["status"] == "partial"
    return {"phase171_apply_confirmation_gate":{"status":"pass" if ready else "not_ready","ready_for_apply":ready,"requires_owner_final_confirm":True,"apply_not_executed":True,"cannot_conclude":["confirmation_gate_is_not_apply","ready_is_not_executed"]}}

def build_coverage_apply_package(validator_output):
    v = validator_output["phase170_schema_validator"] if "phase170_schema_validator" in validator_output else validator_output
    activated = [e for e in v.get("valid",[]) if e["owner_decision"] == "activate_into_formal_research_coverage"]
    kept = [e for e in v.get("valid",[]) if e["owner_decision"] == "keep_as_candidate_pending_more_evidence"]
    deferred = [e for e in v.get("valid",[]) if e["owner_decision"] == "defer_to_next_review_cycle"]
    rejected = [e for e in v.get("valid",[]) if e["owner_decision"] == "reject_from_current_coverage_pipeline"]
    return {"phase171_coverage_apply_package":{"activated_count":len(activated),"kept_count":len(kept),"deferred_count":len(deferred),"rejected_count":len(rejected),"activated":activated,"kept":kept,"deferred":deferred,"rejected":rejected,"apply_not_executed":True,"apply_package_not_activation":True,"cannot_conclude":["apply_package_is_not_apply","coverage_package_is_not_portfolio_action"]}}

def build_state_diff(validator_output):
    v = validator_output["phase170_schema_validator"] if "phase170_schema_validator" in validator_output else validator_output
    diffs = []
    for e in v.get("valid",[]):
        activated = e["owner_decision"] == "activate_into_formal_research_coverage"
        diffs.append({"candidate_id":e["candidate_id"],"current_state":"candidate","proposed_state":"formal_research_coverage" if activated else "candidate","diff_type":"activation" if activated else "no_change","state_not_updated":True,"cannot_conclude":["diff_is_not_state_update"]})
    return {"phase171_state_diff":{"entries":len(diffs),"state_not_updated":True,"diffs":diffs}}

def build_rollback_package():
    return {"phase171_rollback_package":{"rollback_prepared":True,"rollback_steps":["revert_all_coverage_status_to_candidate","revert_tier_assignments","clear_agent_task_queue","restore_previous_state_from_backup"],"rollback_not_apply":True,"cannot_conclude":["rollback_package_is_not_apply"]}}

def build_audit_package(apply_package, state_diff):
    return {"phase171_audit_package":{"audit_entries":apply_package["phase171_coverage_apply_package"]["activated_count"]+apply_package["phase171_coverage_apply_package"]["kept_count"],"audit_trail":["owner_input_read","validation_complete","quarantine_applied","manifest_generated","state_preview_generated","apply_package_generated","audit_not_apply"],"audit_not_execution":True,"cannot_conclude":["audit_is_not_execution"]}}

def build_final_checklist():
    items = [
        "review_all_quarantined_entries","confirm_activated_candidates","confirm_kept_candidates",
        "review_state_diff","acknowledge_rollback_plan","verify_no_trade_language",
        "confirm_no_auto_execution","confirm_owner_manual_apply_required","final_sign_off"
    ]
    return {"phase171_final_checklist":{"items":items,"item_count":len(items),"checklist_not_apply":True}}
