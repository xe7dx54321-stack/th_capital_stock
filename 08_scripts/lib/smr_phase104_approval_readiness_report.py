import json,os
from datetime import datetime
from smr_phase104_approval_domain_registry import build_approval_domain_registry
from smr_phase104_approval_readiness_scorecard import build_approval_readiness_scorecard
def build_approval_readiness_report():
    reg=build_approval_domain_registry()
    sc=build_approval_readiness_scorecard()
    report={
        "generated_at":datetime.now().isoformat(),
        "human_approval_readiness":"partial_ready",
        "assessment_only":True,
        "approval_execution_allowed":False,
        "domains_summary":sc["phase104_approval_readiness_scorecard"],
        "domain_details":reg["phase104_approval_domain_registry"]["domains"],
        "critical_findings":[
            "operator_identity_not_provisioned",
            "two_step_approval_needs_identity_assignment",
            "revocation_audit_trail_incomplete",
            "manual_override_needs_template"
        ],
        "no_order_created":True,
        "no_trade_created":True,
        "no_position_sizing":True,
        "mock_used":False,
        "fixture_used":False
    }
    return {"phase104_approval_readiness_report":report}
