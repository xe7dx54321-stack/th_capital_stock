import json,os
from smr_phase110_assignment_domain_registry import build_assignment_domain_registry
from smr_phase110_manual_assignment_checklist import build_manual_assignment_checklist
def build_assignment_scorecard():
    reg=build_assignment_domain_registry()
    cl=build_manual_assignment_checklist()
    return {"phase110_assignment_scorecard":{"assignment_readiness":"partial_ready","domains_defined":reg["phase110_assignment_domain_registry"]["total_domains"],"roles_assigned":cl["phase110_manual_assignment_checklist"]["assigned"],"roles_required":cl["phase110_manual_assignment_checklist"]["total"],"ready_for_paper_execution":False,"real_operators_assigned":0,"manual_assignment_required":True,"mock_used":False,"fixture_used":False}}
