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
    cfg=load_config();reg=build_approval_domain_registry();pol=build_approval_policy_registry()
    sm=build_approval_state_machine();req=build_approval_request_schema();dec=build_approval_decision_schema()
    ts=build_two_step_approval();exp=build_approval_expiration();rev=build_approval_revocation()
    oi=build_operator_identity();al=build_approval_audit_log_schema();mo=build_manual_override()
    sim=run_no_order_approval_simulation();vc=build_approval_violation_classifier()
    sc=build_approval_readiness_scorecard();rpt=build_approval_readiness_report()
    guard=run_approval_guard();bl=build_backlog_update()
    summary={
        "phase":"phase104","generated_at":datetime.now().isoformat(),
        "assessment_only":cfg["human_approval"]["assessment_only"],
        "approval_execution_allowed":cfg["human_approval"]["approval_execution_allowed"],
        "approval_to_order_allowed":cfg["human_approval"]["approval_to_order_allowed"],
        "order_creation_allowed":cfg["human_approval"]["order_creation_allowed"],
        "position_sizing_allowed":cfg["human_approval"]["position_sizing_allowed"],
        "policies_registered":pol["phase104_approval_policy_registry"]["total_policies"],
        "domains_total":reg["phase104_approval_domain_registry"]["total_domains"],
        "scorecard":sc["phase104_approval_readiness_scorecard"],
        "human_approval_missing":"partially_addressed",
        "kill_switch_missing":"unresolved",
        "risk_control_missing":"partially_addressed",
        "guard":guard["phase104_guard"]["overall"],
        "violations":guard["phase104_guard"]["violations"],
        "blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],
        "no_order_created":True,"no_trade_created":True,"no_position_sizing":True,
        "mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
