import json,os
from datetime import datetime
from smr_phase109_identity_domain_registry import build_identity_domain_registry
from smr_phase109_identity_readiness_checklist import build_identity_readiness_checklist
from smr_phase109_no_order_identity_simulation import run_no_order_identity_simulation
from smr_phase109_identity_readiness_scorecard import build_identity_readiness_scorecard
def build_identity_readiness_report():
    reg=build_identity_domain_registry();cl=build_identity_readiness_checklist()
    sim=run_no_order_identity_simulation();sc=build_identity_readiness_scorecard()
    report={
        "generated_at":datetime.now().isoformat(),
        "identity_readiness":"partial_ready",
        "identity_readiness_only":True,"account_creation_allowed":False,
        "domains":reg["phase109_identity_domain_registry"]["domains"],
        "checklist":cl["phase109_identity_readiness_checklist"],
        "simulation":sim["phase109_no_order_identity_simulation"],
        "scorecard":sc["phase109_identity_readiness_scorecard"],
        "critical_findings":["all_identity_schemas_ready","all_execution_permissions_disabled","3_blockers_require_human_assignment"],
        "account_created":0,"sso_connected":0,"password_saved":0,
        "mock_used":False,"fixture_used":False
    }
    return {"phase109_identity_readiness_report":report}
