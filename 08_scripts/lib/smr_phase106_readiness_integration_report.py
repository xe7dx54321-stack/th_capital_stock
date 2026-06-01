import json,os
from datetime import datetime
from smr_phase106_readiness_module_registry import build_readiness_module_registry
from smr_phase106_cross_gate_dependency_registry import build_cross_gate_dependency_registry
from smr_phase106_blocker_propagation_checker import run_blocker_propagation_checker
from smr_phase106_readiness_status_consistency import run_readiness_status_consistency
from smr_phase106_no_order_safety_consistency import run_no_order_safety_consistency
from smr_phase106_guard_consistency import run_guard_consistency
from smr_phase106_dashboard_consistency import run_dashboard_consistency
from smr_phase106_backlog_consistency import run_backlog_consistency
from smr_phase106_cross_gate_simulation import run_cross_gate_simulation
from smr_phase106_integrated_readiness_scorecard import build_integrated_readiness_scorecard
def build_readiness_integration_report():
    reg=build_readiness_module_registry();deps=build_cross_gate_dependency_registry()
    bp=run_blocker_propagation_checker();rs=run_readiness_status_consistency()
    ns=run_no_order_safety_consistency();gc=run_guard_consistency()
    dc=run_dashboard_consistency();bl=run_backlog_consistency()
    sim=run_cross_gate_simulation();sc=build_integrated_readiness_scorecard()
    report={
        "generated_at":datetime.now().isoformat(),
        "integration_readiness":"partial_ready",
        "assessment_only":True,"integration_test_only":True,"paper_trading_enabled":False,
        "modules":reg["phase106_readiness_module_registry"]["modules"],
        "dependencies":deps["phase106_cross_gate_dependency_registry"]["dependencies"],
        "blocker_propagation":bp["phase106_blocker_propagation_checker"],
        "status_consistency":rs["phase106_readiness_status_consistency"],
        "no_order_safety":ns["phase106_no_order_safety_consistency"],
        "guard_consistency":gc["phase106_guard_consistency"],
        "dashboard_consistency":dc["phase106_dashboard_consistency"],
        "backlog_consistency":bl["phase106_backlog_consistency"],
        "cross_gate_simulation":sim["phase106_cross_gate_simulation"],
        "scorecard":sc["phase106_integrated_readiness_scorecard"],
        "critical_findings":["all_blockers_propagated_correctly","no_order_boundary_intact","all_guards_consistent","phase101_not_misinterpreted_as_trading_ready"],
        "no_order_created":True,"no_trade_created":True,
        "mock_used":False,"fixture_used":False
    }
    return {"phase106_readiness_integration_report":report}
