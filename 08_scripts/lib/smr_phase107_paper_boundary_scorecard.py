import json,os
from smr_phase107_paper_concept_registry import build_paper_concept_registry
from smr_phase107_paper_state_taxonomy import build_paper_state_taxonomy
from smr_phase107_paper_pre_paper_checklist import build_pre_paper_readiness_checklist
def build_paper_boundary_scorecard():
    reg=build_paper_concept_registry()
    st=build_paper_state_taxonomy()
    cl=build_pre_paper_readiness_checklist()
    scorecard={
        "boundary_definition_status":"complete",
        "concepts_defined":reg["phase107_paper_concept_registry"]["total_concepts"],
        "concepts_execution_enabled":0,
        "current_state":st["phase107_paper_state_taxonomy"]["current_state"],
        "paper_execution_reachable":False,
        "checklist_satisfied":cl["phase107_pre_paper_readiness_checklist"]["items_satisfied"],
        "checklist_total":cl["phase107_pre_paper_readiness_checklist"]["total_items"],
        "ready_for_paper_execution":False,
        "paper_order_created":False,"paper_trade_created":False,"paper_pnl_calculated":False,
        "mock_used":False,"fixture_used":False
    }
    return {"phase107_paper_boundary_scorecard":scorecard}
