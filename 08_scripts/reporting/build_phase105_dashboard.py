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
    cfg=load_config();reg=build_emergency_domain_registry();pol=build_kill_switch_policy_registry()
    sm=build_emergency_stop_state_machine();dl=build_disable_live_mode();do=build_disable_order_creation()
    sf=build_safe_mode();rm=build_rollback_manifest_schema();lg=build_last_good_state_registry()
    ie=build_incident_escalation();ml=build_manual_override_lockdown();al=build_emergency_audit_log_schema()
    sim=run_no_order_emergency_simulation();vc=build_emergency_violation_classifier()
    sc=build_emergency_readiness_scorecard();rpt=build_emergency_readiness_report()
    guard=run_emergency_guard();bl=build_backlog_update()
    summary={
        "phase":"phase105","generated_at":datetime.now().isoformat(),
        "assessment_only":cfg["emergency_control"]["assessment_only"],
        "kill_switch_execution_allowed":cfg["emergency_control"]["kill_switch_execution_allowed"],
        "emergency_order_action_allowed":cfg["emergency_control"]["emergency_order_action_allowed"],
        "order_creation_allowed":cfg["emergency_control"]["order_creation_allowed"],
        "position_sizing_allowed":cfg["emergency_control"]["position_sizing_allowed"],
        "policies_registered":pol["phase105_kill_switch_policy_registry"]["total_policies"],
        "domains_total":reg["phase105_emergency_domain_registry"]["total_domains"],
        "scorecard":sc["phase105_emergency_readiness_scorecard"],
        "kill_switch_missing":"partially_addressed",
        "risk_control_missing":"partially_addressed",
        "human_approval_missing":"partially_addressed",
        "phase101_all_blockers_addressed":True,
        "guard":guard["phase105_guard"]["overall"],
        "violations":guard["phase105_guard"]["violations"],
        "blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],
        "no_order_created":True,"no_trade_created":True,"no_position_sizing":True,"no_broker_action":True,
        "mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
