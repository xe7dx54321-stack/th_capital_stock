import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase110_config import load_config
from smr_phase110_assignment_domain_registry import build_assignment_domain_registry
from smr_phase110_role_assignment_matrix import build_role_assignment_matrix
from smr_phase110_assignment_manifest import build_assignment_manifest
from smr_phase110_assignment_input_template import build_assignment_input_template
from smr_phase110_assignment_validation_rules import build_assignment_validation_rules
from smr_phase110_role_conflict_checker import run_role_conflict_checker
from smr_phase110_same_person_assignment_checker import run_same_person_checker
from smr_phase110_dual_control_assignment_checker import run_dual_control_checker
from smr_phase110_supervisor_assignment_checker import run_supervisor_checker
from smr_phase110_kill_switch_operator_checker import run_kill_switch_operator_checker
from smr_phase110_approval_chain_checker import run_approval_chain_checker
from smr_phase110_assignment_audit_log import build_assignment_audit_log
from smr_phase110_manual_assignment_checklist import build_manual_assignment_checklist
from smr_phase110_paper_execution_assignment_dependency import build_paper_execution_dependency
from smr_phase110_no_order_assignment_simulation import run_no_order_assignment_simulation
from smr_phase110_assignment_violation_classifier import build_assignment_violation_classifier
from smr_phase110_assignment_readiness_scorecard import build_assignment_scorecard
from smr_phase110_assignment_readiness_report import build_assignment_report
from smr_phase110_assignment_cannot_conclude_guard import run_assignment_guard
from smr_phase110_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    reg=build_assignment_domain_registry();steps.append({"name":"domain_registry","status":"ok","detail":f"domains={reg['phase110_assignment_domain_registry']['total_domains']}"})
    rm=build_role_assignment_matrix();steps.append({"name":"role_matrix","status":"ok","detail":f"roles={rm['phase110_role_assignment_matrix']['required_roles']}"})
    mf=build_assignment_manifest();steps.append({"name":"manifest","status":"ok"})
    tp=build_assignment_input_template();steps.append({"name":"input_template","status":"ok"})
    vr=build_assignment_validation_rules();steps.append({"name":"validation_rules","status":"ok"})
    rc=run_role_conflict_checker();steps.append({"name":"role_conflict","status":"ok"})
    sp=run_same_person_checker();steps.append({"name":"same_person","status":"ok"})
    dc=run_dual_control_checker();steps.append({"name":"dual_control","status":"ok"})
    su=run_supervisor_checker();steps.append({"name":"supervisor","status":"ok","detail":su["phase110_supervisor_checker"]["status"]})
    ks=run_kill_switch_operator_checker();steps.append({"name":"kill_switch_op","status":"ok","detail":ks["phase110_kill_switch_operator_checker"]["status"]})
    ac=run_approval_chain_checker();steps.append({"name":"approval_chain","status":"ok"})
    al=build_assignment_audit_log();steps.append({"name":"audit_log","status":"ok"})
    cl=build_manual_assignment_checklist();steps.append({"name":"checklist","status":"ok","detail":f"assigned={cl['phase110_manual_assignment_checklist']['assigned']}/{cl['phase110_manual_assignment_checklist']['total']}"})
    pe=build_paper_execution_dependency();steps.append({"name":"paper_exec_dep","status":"ok","detail":pe["phase110_paper_execution_dependency"]["blocked_by"]})
    sim=run_no_order_assignment_simulation();steps.append({"name":"simulation","status":"ok","detail":f"violations={sim['phase110_no_order_simulation']['violations']}"})
    vc=build_assignment_violation_classifier();steps.append({"name":"violation_classifier","status":"ok"})
    sc=build_assignment_scorecard();steps.append({"name":"scorecard","status":"ok","detail":sc["phase110_assignment_scorecard"]["assignment_readiness"]})
    rpt=build_assignment_report();steps.append({"name":"assignment_report","status":"ok"})
    guard=run_assignment_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase110_guard"]["overall"]})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={"phase110_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),"assessment_only":True,"manual_assignment_only":True,"auto_assignment_allowed":False,"account_creation_allowed":False,"paper_execution_enabled":False,"domains_defined":reg["phase110_assignment_domain_registry"]["total_domains"],"roles_defined":rm["phase110_role_assignment_matrix"]["required_roles"],"real_operators_assigned":0,"ready_for_paper_execution":False,"guard":guard["phase110_guard"]["overall"],"violations":guard["phase110_guard"]["violations"],"steps":steps,"account_created":0,"sso_connected":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
