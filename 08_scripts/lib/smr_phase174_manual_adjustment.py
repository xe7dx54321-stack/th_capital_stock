# Phase174 manual adjustment workflow
from smr_phase174_coverage_state_registry import build_coverage_state_registry, CANDIDATES

def build_manual_adjustment_workflow():
    registry = build_coverage_state_registry()
    r = registry["phase174_coverage_state_registry"]
    workflow = []
    for e in r["entries"]:
        cid = e["candidate_id"]
        tier = e["coverage_tier"]
        allowed_actions = []
        if tier == "formal_research_coverage":
            allowed_actions = ["pause_monitoring","downgrade_to_candidate_pending","mark_thesis_changed"]
        elif tier == "candidate_pending":
            allowed_actions = ["upgrade_to_formal_coverage","keep_pending","reject"]
        elif tier == "deferred_review":
            allowed_actions = ["advance_review","keep_deferred","reject"]
        elif tier == "rejected":
            allowed_actions = ["reconsider_with_new_evidence","keep_rejected"]
        workflow.append({
            "candidate_id":cid,"current_tier":tier,
            "allowed_manual_actions":allowed_actions,
            "manual_adjustment_does_not_execute_apply":True,
            "requires_owner_confirmation":True,
            "cannot_conclude":["manual_adjustment_recommends_not_executes"]
        })
    return {"phase174_manual_adjustment_workflow":{
        "manual_adjustment_enabled":True,
        "candidates_with_workflow":len(workflow),
        "workflow":workflow,
        "manual_adjustment_not_auto_apply":True,
        "manual_adjustment_requires_owner":True,
        "mock_used":False,"fixture_used":False
    }}
