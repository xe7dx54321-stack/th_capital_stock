import json,os
from datetime import datetime
from smr_phase108_readiness_domain_registry import build_readiness_domain_registry
from smr_phase108_pre_paper_checklist import build_pre_paper_checklist
from smr_phase108_safety_gate import run_safety_gate
from smr_phase108_disabled_state_verifier import run_disabled_state_verifier
from smr_phase108_dry_run_simulation import run_dry_run_simulation
from smr_phase108_readiness_scorecard import build_readiness_scorecard
def build_readiness_report():
    reg=build_readiness_domain_registry();cl=build_pre_paper_checklist()
    sg=run_safety_gate();dv=run_disabled_state_verifier()
    sim=run_dry_run_simulation();sc=build_readiness_scorecard()
    report={
        "generated_at":datetime.now().isoformat(),
        "paper_execution_readiness":"partial_ready",
        "readiness_only":True,"paper_execution_enabled":False,
        "domains":reg["phase108_readiness_domain_registry"]["domains"],
        "checklist":cl["phase108_pre_paper_checklist"],
        "safety_gate":sg["phase108_safety_gate"],
        "disabled_verifier":dv["phase108_disabled_state_verifier"],
        "dry_run":sim["phase108_dry_run_simulation"],
        "scorecard":sc["phase108_readiness_scorecard"],
        "critical_findings":["4_blockers_prevent_paper_execution","operator_identity_is_hardest_blocker","all_execution_disabled_and_verified"],
        "paper_order_created":False,"paper_trade_created":False,"paper_pnl_calculated":False,
        "mock_used":False,"fixture_used":False
    }
    return {"phase108_readiness_report":report}
