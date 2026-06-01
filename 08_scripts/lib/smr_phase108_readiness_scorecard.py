import json,os
from smr_phase108_readiness_domain_registry import build_readiness_domain_registry
from smr_phase108_pre_paper_checklist import build_pre_paper_checklist
def build_readiness_scorecard():
    reg=build_readiness_domain_registry()
    cl=build_pre_paper_checklist()
    scorecard={
        "paper_execution_readiness":"partial_ready",
        "domains_assessed":reg["phase108_readiness_domain_registry"]["total_domains"],
        "checklist_satisfied":cl["phase108_pre_paper_checklist"]["items_satisfied"],
        "checklist_total":cl["phase108_pre_paper_checklist"]["items_total"],
        "ready_for_paper_execution":False,
        "blockers_remaining":cl["phase108_pre_paper_checklist"]["blockers"],
        "paper_order_created":False,"paper_trade_created":False,"paper_pnl_calculated":False,
        "next_step":"resolve_blockers_then_phase109_paper_execution_activation",
        "mock_used":False,"fixture_used":False
    }
    return {"phase108_readiness_scorecard":scorecard}
