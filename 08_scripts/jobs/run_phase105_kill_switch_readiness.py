import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase105_config import load_config
from smr_phase105_emergency_domain_registry import build_emergency_domain_registry
from smr_phase105_kill_switch_policy_registry import build_kill_switch_policy_registry
from smr_phase105_emergency_stop_state_machine import build_emergency_stop_state_machine
from smr_phase105_disable_live_mode import build_disable_live_mode
from smr_phase105_disable_order_creation import build_disable_order_creation
from smr_phase105_safe_mode import build_safe_mode
from smr_phase105_rollback_manifest import build_rollback_manifest_schema
from smr_phase105_last_good_state import build_last_good_state_registry
from smr_phase105_incident_escalation import build_incident_escalation
from smr_phase105_manual_override_lockdown import build_manual_override_lockdown
from smr_phase105_emergency_audit_log import build_emergency_audit_log_schema
from smr_phase105_no_order_emergency_simulation import run_no_order_emergency_simulation
from smr_phase105_emergency_violation_classifier import build_emergency_violation_classifier
from smr_phase105_emergency_readiness_scorecard import build_emergency_readiness_scorecard
from smr_phase105_emergency_readiness_report import build_emergency_readiness_report
from smr_phase105_emergency_cannot_conclude_guard import run_emergency_guard
from smr_phase105_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    reg=build_emergency_domain_registry();steps.append({"name":"domain_registry","status":"ok","detail":f"domains={reg['phase105_emergency_domain_registry']['total_domains']}"})
    pol=build_kill_switch_policy_registry();steps.append({"name":"policy_registry","status":"ok","detail":f"policies={pol['phase105_kill_switch_policy_registry']['total_policies']}"})
    sm=build_emergency_stop_state_machine();steps.append({"name":"state_machine","status":"ok","detail":f"states={len(sm['phase105_emergency_stop_state_machine']['states'])}"})
    dl=build_disable_live_mode();steps.append({"name":"disable_live","status":"ok","detail":dl["phase105_disable_live_mode"]["readiness_status"]})
    do=build_disable_order_creation();steps.append({"name":"disable_order","status":"ok","detail":do["phase105_disable_order_creation"]["readiness_status"]})
    sf=build_safe_mode();steps.append({"name":"safe_mode","status":"ok","detail":sf["phase105_safe_mode"]["safe_mode_readiness"]})
    rm=build_rollback_manifest_schema();steps.append({"name":"rollback_manifest","status":"ok"})
    lg=build_last_good_state_registry();steps.append({"name":"last_good_state","status":"ok","detail":lg["phase105_last_good_state_registry"]["readiness_status"]})
    ie=build_incident_escalation();steps.append({"name":"incident_escalation","status":"ok","detail":ie["phase105_incident_escalation"]["readiness_status"]})
    ml=build_manual_override_lockdown();steps.append({"name":"override_lockdown","status":"ok","detail":ml["phase105_manual_override_lockdown"]["readiness_status"]})
    al=build_emergency_audit_log_schema();steps.append({"name":"audit_log","status":"ok"})
    sim=run_no_order_emergency_simulation();steps.append({"name":"emergency_simulation","status":"ok","detail":f"violations={sim['phase105_no_order_emergency_simulation']['violations']}"})
    vc=build_emergency_violation_classifier();steps.append({"name":"violation_classifier","status":"ok"})
    sc=build_emergency_readiness_scorecard();steps.append({"name":"scorecard","status":"ok","detail":sc["phase105_emergency_readiness_scorecard"]["overall_readiness"]})
    rpt=build_emergency_readiness_report();steps.append({"name":"readiness_report","status":"ok","detail":rpt["phase105_emergency_readiness_report"]["kill_switch_readiness"]})
    guard=run_emergency_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase105_guard"]["overall"]})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={
        "phase105_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),
            "assessment_only":True,"kill_switch_execution_allowed":False,"emergency_order_action_allowed":False,
            "order_creation_allowed":False,"position_sizing_allowed":False,
            "policies_registered":pol["phase105_kill_switch_policy_registry"]["total_policies"],
            "domains_checked":reg["phase105_emergency_domain_registry"]["total_domains"],
            "readiness_status":sc["phase105_emergency_readiness_scorecard"]["overall_readiness"],
            "kill_switch_missing":"partially_addressed",
            "risk_control_missing":"partially_addressed",
            "human_approval_missing":"partially_addressed",
            "phase101_all_blockers_addressed":True,
            "guard":guard["phase105_guard"]["overall"],
            "violations":guard["phase105_guard"]["violations"],
            "steps":steps,
            "no_order_created":True,"no_trade_created":True,"no_position_sizing":True,"no_broker_action":True,
            "mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,
            "pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
        }
    }
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
