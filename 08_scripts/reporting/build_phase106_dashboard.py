import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase106_config import load_config
from smr_phase106_readiness_module_registry import build_readiness_module_registry
from smr_phase106_phase_status_loader import load_all_phase_status
from smr_phase106_cross_gate_dependency_registry import build_cross_gate_dependency_registry
from smr_phase106_blocker_propagation_checker import run_blocker_propagation_checker
from smr_phase106_readiness_status_consistency import run_readiness_status_consistency
from smr_phase106_no_order_safety_consistency import run_no_order_safety_consistency
from smr_phase106_guard_consistency import run_guard_consistency
from smr_phase106_dashboard_consistency import run_dashboard_consistency
from smr_phase106_backlog_consistency import run_backlog_consistency
from smr_phase106_cross_gate_simulation import run_cross_gate_simulation
from smr_phase106_integration_violation_classifier import build_integration_violation_classifier
from smr_phase106_integrated_readiness_scorecard import build_integrated_readiness_scorecard
from smr_phase106_readiness_integration_report import build_readiness_integration_report
from smr_phase106_integration_quality_gate import run_integration_quality_gate
from smr_phase106_integration_cannot_conclude_guard import run_integration_guard
from smr_phase106_backlog_update import build_backlog_update
def main():
    cfg=load_config();reg=build_readiness_module_registry();st=load_all_phase_status()
    deps=build_cross_gate_dependency_registry();bp=run_blocker_propagation_checker()
    rs=run_readiness_status_consistency();ns=run_no_order_safety_consistency()
    gc=run_guard_consistency();dc=run_dashboard_consistency();bl=run_backlog_consistency()
    sim=run_cross_gate_simulation();vc=build_integration_violation_classifier()
    sc=build_integrated_readiness_scorecard();rpt=build_readiness_integration_report()
    gate=run_integration_quality_gate(bp,rs,ns,gc,dc,bl,sim)
    guard=run_integration_guard();backlog=build_backlog_update()
    summary={
        "phase":"phase106","generated_at":datetime.now().isoformat(),
        "assessment_only":cfg["integration"]["assessment_only"],
        "integration_test_only":cfg["integration"]["integration_test_only"],
        "paper_trading_enabled":cfg["integration"]["paper_trading_enabled"],
        "live_trading_enabled":cfg["integration"]["live_trading_enabled"],
        "order_creation_allowed":cfg["integration"]["order_creation_allowed"],
        "position_sizing_allowed":cfg["integration"]["position_sizing_allowed"],
        "modules_assessed":reg["phase106_readiness_module_registry"]["total_modules"],
        "dependencies_registered":deps["phase106_cross_gate_dependency_registry"]["total_dependencies"],
        "scorecard":sc["phase106_integrated_readiness_scorecard"],
        "quality_gate":gate["phase106_integration_quality_gate"]["overall"],
        "guard":guard["phase106_guard"]["overall"],"violations":guard["phase106_guard"]["violations"],
        "blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],
        "no_order_created":True,"no_trade_created":True,"no_position_sizing":True,
        "mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
