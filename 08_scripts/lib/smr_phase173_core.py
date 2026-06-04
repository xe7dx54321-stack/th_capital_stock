CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]
ACTIVATE = ["TSM","ASML","MRVL","AMAT","LRCX","KLAC","CDNS","CRM","AMD"]
KEEP = ["INTC","MU"]
DEFER = ["SNPS"]
REJECT = ["SNOW"]

def build_candidate_recommendation_draft():
    recs = []
    for tk in CANDIDATES:
        if tk in ACTIVATE: d = "activate_into_formal_research_coverage"
        elif tk in KEEP: d = "keep_as_candidate_pending_more_evidence"
        elif tk in DEFER: d = "defer_to_next_review_cycle"
        else: d = "reject_from_current_coverage_pipeline"
        recs.append({"candidate_id":tk,"recommended_decision":d,"recommendation_not_approval":True,"recommendation_not_trade":True,"cannot_conclude":["recommendation_is_not_owner_decision","draft_is_not_final"]})
    return {"phase173_candidate_recommendation_draft":{"entries":len(recs),"activated":len(ACTIVATE),"kept":len(KEEP),"deferred":len(DEFER),"rejected":len(REJECT),"recommendations":recs,"recommendation_not_approval":True,"recommendation_not_trade":True}}

def build_fill_ready_json_draft():
    decisions = []
    for tk in CANDIDATES:
        if tk in ACTIVATE: d = "activate_into_formal_research_coverage"; r = "Evidence complete; agent rerun passed; thesis identified."
        elif tk in KEEP: d = "keep_as_candidate_pending_more_evidence"; r = "Requires additional milestone evidence before activation."
        elif tk in DEFER: d = "defer_to_next_review_cycle"; r = "Binary event pending; defer to avoid pre-judgment."
        else: d = "reject_from_current_coverage_pipeline"; r = "Current evidence insufficient for formal coverage."
        decisions.append({"candidate_id":tk,"owner_decision":d,"rationale":r,"conditions":["tier_assignment_required","owner_review_required"],"risk_acknowledgment":"Standard research risk; no trade recommendation implied."})
    draft_json = {"decisions":decisions,"draft_not_real_input":True,"auto_write_disabled":True}
    return {"phase173_fill_ready_json_draft":{"draft_generated":True,"draft_not_real_input":True,"auto_write_disabled":True,"draft_json":draft_json}}

def build_preflight_checklist():
    items = [
        "review_all_13_recommendations","adjust_decisions_per_owner_knowledge",
        "verify_no_buy_sell_hold_in_any_field","verify_no_target_price_in_any_field",
        "verify_no_position_sizing_in_any_field","fill_rationale_with_research_evidence",
        "fill_risk_acknowledgment_with_specific_risks","copy_draft_to_owner_decision_input.json",
        "run_preflight: python 08_scripts/jobs/run_phase169_authoring_guide_pipeline.py --execute --json",
        "run_validation: python 08_scripts/jobs/run_phase170_owner_input_validation_pipeline.py --execute --json",
        "run_apply_preview: python 08_scripts/jobs/run_phase172_coverage_apply_pipeline.py --execute --json",
        "review_state_diff: verify proposed changes match intent",
        "sign_owner_final_confirmation.json",
        "run_apply: python 08_scripts/jobs/run_phase172_coverage_apply_pipeline.py --execute --execute-apply --json"
    ]
    return {"phase173_preflight_checklist":{"items":items,"item_count":len(items),"checklist_not_auto":True}}

def build_final_confirmation_pack():
    return {"phase173_final_confirmation_pack":{"confirmation_fields":["owner_name","confirmation_date","decisions_confirmed","checklist_completed","rollback_acknowledged","final_signature"],"confirmation_not_auto":True,"confirmation_requires_owner_signature":True,"cannot_conclude":["confirmation_is_not_auto_approval","signature_is_not_system_generated"]}}

def build_execute_apply_instructions():
    return {"phase173_execute_apply_instructions":{
        "step_1":"Copy draft from phase173_fill_ready_json_draft to 09_runbooks/generated/phase168_owner_decision_manual_submission/owner_decision_input.json",
        "step_2":"Edit decisions per owner knowledge",
        "step_3":"Run preflight: python 08_scripts/jobs/run_phase169_authoring_guide_pipeline.py --execute --json",
        "step_4":"Run validation: python 08_scripts/jobs/run_phase170_owner_input_validation_pipeline.py --execute --json",
        "step_5":"Review state preview and confirm",
        "step_6":"Execute apply: python 08_scripts/jobs/run_phase172_coverage_apply_pipeline.py --execute --execute-apply --json",
        "DO_NOT_auto_execute":True,"DO_NOT_skip_owner_review":True
    }}
