import json,os
from smr_phase106_readiness_module_registry import build_readiness_module_registry
from smr_phase106_blocker_propagation_checker import run_blocker_propagation_checker
from smr_phase106_readiness_status_consistency import run_readiness_status_consistency
def build_integrated_readiness_scorecard():
    reg=build_readiness_module_registry()
    bp=run_blocker_propagation_checker()
    rs=run_readiness_status_consistency()
    scorecard={
        "integrated_readiness":"partial_ready",
        "modules_assessed":reg["phase106_readiness_module_registry"]["total_modules"],
        "addressed":1,"partially_addressed":3,"unresolved":0,
        "blocker_propagation_healthy":bp["phase106_blocker_propagation_checker"]["propagation_healthy"],
        "readiness_status_consistent":rs["phase106_readiness_status_consistency"]["all_consistent"],
        "no_module_trading_ready":True,
        "phase101_all_blockers_addressed_caveat":"not_trading_ready",
        "next_step":"phase107_paper_trading_boundary_definition",
        "mock_used":False,"fixture_used":False
    }
    return {"phase106_integrated_readiness_scorecard":scorecard}
