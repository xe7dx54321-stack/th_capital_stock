import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase104_config import load_config
from smr_phase104_approval_domain_registry import build_approval_domain_registry
from smr_phase104_approval_policy_registry import build_approval_policy_registry
from smr_phase104_approval_state_machine import build_approval_state_machine
from smr_phase104_approval_request_schema import build_approval_request_schema
from smr_phase104_approval_decision_schema import build_approval_decision_schema
from smr_phase104_two_step_approval import build_two_step_approval
from smr_phase104_approval_expiration import build_approval_expiration
from smr_phase104_approval_revocation import build_approval_revocation
from smr_phase104_operator_identity import build_operator_identity
from smr_phase104_approval_audit_log import build_approval_audit_log_schema
from smr_phase104_manual_override import build_manual_override
from smr_phase104_no_order_approval_simulation import run_no_order_approval_simulation
from smr_phase104_approval_violation_classifier import build_approval_violation_classifier
from smr_phase104_approval_readiness_scorecard import build_approval_readiness_scorecard
from smr_phase104_approval_readiness_report import build_approval_readiness_report
from smr_phase104_approval_cannot_conclude_guard import run_approval_guard
from smr_phase104_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    reg=build_approval_domain_registry();steps.append({"name":"domain_registry","status":"ok","detail":f"domains={reg['phase104_approval_domain_registry']['total_domains']}"})
    pol=build_approval_policy_registry();steps.append({"name":"policy_registry","status":"ok","detail":f"policies={pol['phase104_approval_policy_registry']['total_policies']}"})
    sm=build_approval_state_machine();steps.append({"name":"state_machine","status":"ok"})
    req=build_approval_request_schema();steps.append({"name":"request_schema","status":"ok"})
    dec=build_approval_decision_schema();steps.append({"name":"decision_schema","status":"ok"})
    ts=build_two_step_approval();steps.append({"name":"two_step_approval","status":"ok","detail":ts["phase104_two_step_approval"]["readiness_status"]})
    exp=build_approval_expiration();steps.append({"name":"expiration","status":"ok","detail":exp["phase104_approval_expiration"]["readiness_status"]})
    rev=build_approval_revocation();steps.append({"name":"revocation","status":"ok","detail":rev["phase104_approval_revocation"]["readiness_status"]})
    oi=build_operator_identity();steps.append({"name":"operator_identity","status":"ok","detail":oi["phase104_operator_identity"]["readiness_status"]})
    al=build_approval_audit_log_schema();steps.append({"name":"audit_log","status":"ok"})
    mo=build_manual_override();steps.append({"name":"manual_override","status":"ok","detail":mo["phase104_manual_override"]["readiness_status"]})
    sim=run_no_order_approval_simulation();steps.append({"name":"no_order_simulation","status":"ok","detail":f"violations={sim['phase104_no_order_approval_simulation']['violations']}"})
    vc=build_approval_violation_classifier();steps.append({"name":"violation_classifier","status":"ok"})
    sc=build_approval_readiness_scorecard();steps.append({"name":"scorecard","status":"ok","detail":sc["phase104_approval_readiness_scorecard"]["overall_readiness"]})
    rpt=build_approval_readiness_report();steps.append({"name":"readiness_report","status":"ok","detail":rpt["phase104_approval_readiness_report"]["human_approval_readiness"]})
    guard=run_approval_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase104_guard"]["overall"]})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={
        "phase104_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),
            "assessment_only":True,"approval_execution_allowed":False,"approval_to_order_allowed":False,
            "order_creation_allowed":False,"position_sizing_allowed":False,
            "policies_registered":pol["phase104_approval_policy_registry"]["total_policies"],
            "domains_checked":reg["phase104_approval_domain_registry"]["total_domains"],
            "readiness_status":sc["phase104_approval_readiness_scorecard"]["overall_readiness"],
            "human_approval_missing":"partially_addressed",
            "kill_switch_missing":"unresolved",
            "guard":guard["phase104_guard"]["overall"],
            "violations":guard["phase104_guard"]["violations"],
            "steps":steps,
            "no_order_created":True,"no_trade_created":True,"no_position_sizing":True,
            "mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,
            "pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
        }
    }
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
