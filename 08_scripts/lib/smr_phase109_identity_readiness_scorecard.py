import json,os
from smr_phase109_identity_domain_registry import build_identity_domain_registry
from smr_phase109_identity_readiness_checklist import build_identity_readiness_checklist
def build_identity_readiness_scorecard():
    reg=build_identity_domain_registry()
    cl=build_identity_readiness_checklist()
    scorecard={
        "identity_readiness":"partial_ready",
        "domains_defined":reg["phase109_identity_domain_registry"]["total_domains"],
        "checklist_satisfied":cl["phase109_identity_readiness_checklist"]["satisfied"],
        "checklist_total":cl["phase109_identity_readiness_checklist"]["total"],
        "operator_identity_missing":"partially_addressed",
        "same_operator_forbidden_missing":"addressed",
        "dual_control_missing":"addressed",
        "identity_audit_missing":"addressed",
        "ready_for_paper_execution":False,
        "account_created":0,"sso_connected":0,"password_saved":0,
        "mock_used":False,"fixture_used":False
    }
    return {"phase109_identity_readiness_scorecard":scorecard}
