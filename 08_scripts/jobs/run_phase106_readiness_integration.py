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
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    reg=build_readiness_module_registry();steps.append({"name":"module_registry","status":"ok","detail":f"modules={reg['phase106_readiness_module_registry']['total_modules']}"})
    st=load_all_phase_status();steps.append({"name":"phase_status_loader","status":"ok"})
    deps=build_cross_gate_dependency_registry();steps.append({"name":"dependency_registry","status":"ok","detail":f"deps={deps['phase106_cross_gate_dependency_registry']['total_dependencies']}"})
    bp=run_blocker_propagation_checker();steps.append({"name":"blocker_propagation","status":"ok","detail":f"inconsistent={bp['phase106_blocker_propagation_checker']['inconsistent']}"})
    rs=run_readiness_status_consistency();steps.append({"name":"status_consistency","status":"ok"})
    ns=run_no_order_safety_consistency();steps.append({"name":"no_order_safety","status":"ok","detail":f"inconsistent={ns['phase106_no_order_safety_consistency']['inconsistent']}"})
    gc=run_guard_consistency();steps.append({"name":"guard_consistency","status":"ok"})
    dc=run_dashboard_consistency();steps.append({"name":"dashboard_consistency","status":"ok"})
    bl=run_backlog_consistency();steps.append({"name":"backlog_consistency","status":"ok"})
    sim=run_cross_gate_simulation();steps.append({"name":"cross_gate_simulation","status":"ok","detail":f"violations={sim['phase106_cross_gate_simulation']['violations']}"})
    vc=build_integration_violation_classifier();steps.append({"name":"violation_classifier","status":"ok"})
    sc=build_integrated_readiness_scorecard();steps.append({"name":"scorecard","status":"ok","detail":sc["phase106_integrated_readiness_scorecard"]["integrated_readiness"]})
    rpt=build_readiness_integration_report();steps.append({"name":"integration_report","status":"ok"})
    gate=run_integration_quality_gate(bp,rs,ns,gc,dc,bl,sim);steps.append({"name":"quality_gate","status":"ok","detail":gate["phase106_integration_quality_gate"]["overall"]})
    guard=run_integration_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase106_guard"]["overall"]})
    backlog=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={
        "phase106_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),
            "assessment_only":True,"integration_test_only":True,"paper_trading_enabled":False,"live_trading_enabled":False,
            "order_creation_allowed":False,"position_sizing_allowed":False,
            "modules_assessed":reg["phase106_readiness_module_registry"]["total_modules"],
            "dependencies_registered":deps["phase106_cross_gate_dependency_registry"]["total_dependencies"],
            "integrated_readiness":sc["phase106_integrated_readiness_scorecard"]["integrated_readiness"],
            "quality_gate":gate["phase106_integration_quality_gate"]["overall"],
            "guard":guard["phase106_guard"]["overall"],"violations":guard["phase106_guard"]["violations"],
            "steps":steps,
            "no_order_created":True,"no_trade_created":True,"no_position_sizing":True,
            "mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,
            "pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
        }
    }
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
