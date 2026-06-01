import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase109_config import load_config
from smr_phase109_identity_domain_registry import build_identity_domain_registry
from smr_phase109_operator_identity_schema import build_operator_identity_schema
from smr_phase109_operator_role_registry import build_operator_role_registry
from smr_phase109_permission_matrix import build_permission_matrix
from smr_phase109_approval_role_binding import build_approval_role_binding
from smr_phase109_supervisor_identity import build_supervisor_identity
from smr_phase109_dual_control_rule import build_dual_control_rule
from smr_phase109_same_operator_forbidden import build_same_operator_forbidden
from smr_phase109_manual_override_identity import build_manual_override_identity
from smr_phase109_kill_switch_operator_identity import build_kill_switch_operator_identity
from smr_phase109_paper_execution_identity_dependency import build_paper_execution_identity_dependency
from smr_phase109_identity_audit_log import build_identity_audit_log_schema
from smr_phase109_identity_provisioning_manifest import build_identity_provisioning_manifest
from smr_phase109_identity_readiness_checklist import build_identity_readiness_checklist
from smr_phase109_no_order_identity_simulation import run_no_order_identity_simulation
from smr_phase109_identity_violation_classifier import build_identity_violation_classifier
from smr_phase109_identity_readiness_scorecard import build_identity_readiness_scorecard
from smr_phase109_identity_readiness_report import build_identity_readiness_report
from smr_phase109_identity_cannot_conclude_guard import run_identity_guard
from smr_phase109_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    reg=build_identity_domain_registry();steps.append({"name":"domain_registry","status":"ok","detail":f"domains={reg['phase109_identity_domain_registry']['total_domains']}"})
    scm=build_operator_identity_schema();steps.append({"name":"identity_schema","status":"ok"})
    roles=build_operator_role_registry();steps.append({"name":"role_registry","status":"ok","detail":f"roles={roles['phase109_operator_role_registry']['total_roles']}"})
    pm=build_permission_matrix();steps.append({"name":"permission_matrix","status":"ok","detail":"all_execution_disabled"})
    ab=build_approval_role_binding();steps.append({"name":"approval_binding","status":"ok"})
    si=build_supervisor_identity();steps.append({"name":"supervisor_identity","status":"ok","detail":si["phase109_supervisor_identity"]["readiness_status"]})
    dc=build_dual_control_rule();steps.append({"name":"dual_control","status":"ok"})
    sf=build_same_operator_forbidden();steps.append({"name":"same_operator_forbidden","status":"ok"})
    mo=build_manual_override_identity();steps.append({"name":"manual_override","status":"ok"})
    ks=build_kill_switch_operator_identity();steps.append({"name":"kill_switch_operator","status":"ok","detail":ks["phase109_kill_switch_operator_identity"]["readiness_status"]})
    pe=build_paper_execution_identity_dependency();steps.append({"name":"paper_execution_dependency","status":"ok","detail":pe["phase109_paper_execution_identity_dependency"]["blocker_status"]})
    al=build_identity_audit_log_schema();steps.append({"name":"audit_log","status":"ok"})
    ip=build_identity_provisioning_manifest();steps.append({"name":"provisioning_manifest","status":"ok"})
    cl=build_identity_readiness_checklist();steps.append({"name":"checklist","status":"ok","detail":f"satisfied={cl['phase109_identity_readiness_checklist']['satisfied']}/{cl['phase109_identity_readiness_checklist']['total']}"})
    sim=run_no_order_identity_simulation();steps.append({"name":"simulation","status":"ok","detail":f"violations={sim['phase109_no_order_identity_simulation']['violations']}"})
    vc=build_identity_violation_classifier();steps.append({"name":"violation_classifier","status":"ok"})
    sc=build_identity_readiness_scorecard();steps.append({"name":"scorecard","status":"ok","detail":sc["phase109_identity_readiness_scorecard"]["identity_readiness"]})
    rpt=build_identity_readiness_report();steps.append({"name":"readiness_report","status":"ok"})
    guard=run_identity_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase109_guard"]["overall"]})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={
        "phase109_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),
            "assessment_only":True,"identity_readiness_only":True,"account_creation_allowed":False,"sso_integration_allowed":False,
            "paper_execution_enabled":False,
            "domains_defined":reg["phase109_identity_domain_registry"]["total_domains"],
            "roles_defined":roles["phase109_operator_role_registry"]["total_roles"],
            "operator_identity_missing":"partially_addressed",
            "ready_for_paper_execution":False,
            "guard":guard["phase109_guard"]["overall"],"violations":guard["phase109_guard"]["violations"],
            "steps":steps,
            "account_created":0,"sso_connected":0,"password_saved":0,"paper_order_created":0,
            "mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,
            "pending_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
        }
    }
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
