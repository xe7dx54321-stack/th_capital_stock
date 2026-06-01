import json,os
from datetime import datetime
from smr_phase110_assignment_domain_registry import build_assignment_domain_registry
from smr_phase110_manual_assignment_checklist import build_manual_assignment_checklist
from smr_phase110_no_order_assignment_simulation import run_no_order_assignment_simulation
from smr_phase110_assignment_readiness_scorecard import build_assignment_scorecard
def build_assignment_report():
    reg=build_assignment_domain_registry();cl=build_manual_assignment_checklist()
    sim=run_no_order_assignment_simulation();sc=build_assignment_scorecard()
    return {"phase110_assignment_report":{"generated_at":datetime.now().isoformat(),"assignment_readiness":"partial_ready","manual_assignment_only":True,"domains":reg["phase110_assignment_domain_registry"]["domains"],"checklist":cl["phase110_manual_assignment_checklist"],"simulation":sim["phase110_no_order_simulation"],"scorecard":sc["phase110_assignment_scorecard"],"critical_findings":["all_schema_ready","0_operators_assigned","6_slots_require_human_fill"],"real_operators_assigned":0,"mock_used":False,"fixture_used":False}}
