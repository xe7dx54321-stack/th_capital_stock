import json,os
from datetime import datetime
from smr_phase105_emergency_domain_registry import build_emergency_domain_registry
from smr_phase105_emergency_readiness_scorecard import build_emergency_readiness_scorecard
def build_emergency_readiness_report():
    reg=build_emergency_domain_registry()
    sc=build_emergency_readiness_scorecard()
    report={
        "generated_at":datetime.now().isoformat(),
        "kill_switch_readiness":"partial_ready",
        "assessment_only":True,
        "kill_switch_execution_allowed":False,
        "domains_summary":sc["phase105_emergency_readiness_scorecard"],
        "domain_details":reg["phase105_emergency_domain_registry"]["domains"],
        "critical_findings":[
            "rollback_manifest_schema_defined_but_procedure_not_tested",
            "last_good_state_registry_needs_automated_snapshot",
            "incident_escalation_needs_contact_roster",
            "emergency_guardrail_needs_severity_levels"
        ],
        "no_order_created":True,"no_trade_created":True,"no_position_sizing":True,"no_broker_action":True,
        "mock_used":False,"fixture_used":False
    }
    return {"phase105_emergency_readiness_report":report}
