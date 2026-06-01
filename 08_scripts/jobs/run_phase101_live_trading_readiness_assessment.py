import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase101_config import load_config
from smr_phase101_domain_registry import build_domain_registry
from smr_phase101_phase100_baseline import capture_phase100_baseline
from smr_phase101_data_source_readiness import assess_data_source_readiness
from smr_phase101_hard_data_db_readiness import assess_hard_data_db_readiness
from smr_phase101_production_monitoring_readiness import assess_production_monitoring_readiness
from smr_phase101_evidence_signal_readiness import assess_evidence_signal_readiness
from smr_phase101_risk_control_readiness import assess_risk_control_readiness
from smr_phase101_paper_live_readiness import assess_paper_live_readiness
from smr_phase101_human_approval_readiness import assess_human_approval_readiness
from smr_phase101_execution_lockdown_readiness import assess_execution_lockdown_readiness
from smr_phase101_audit_log_readiness import assess_audit_log_readiness
from smr_phase101_emergency_control_readiness import assess_emergency_control_readiness
from smr_phase101_compliance_guardrail_readiness import assess_compliance_guardrail_readiness
from smr_phase101_system_stability_readiness import assess_system_stability_readiness
from smr_phase101_scorecard import build_scorecard
from smr_phase101_go_no_go import build_go_no_go
from smr_phase101_markdown_report import build_markdown_report
from smr_phase101_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    baseline=capture_phase100_baseline();steps.append({"name":"phase100_baseline","status":"ok"})
    reg=build_domain_registry();steps.append({"name":"domain_registry","status":"ok"})
    assessments=[assess_data_source_readiness(),assess_hard_data_db_readiness(),assess_production_monitoring_readiness(),assess_evidence_signal_readiness(),assess_risk_control_readiness(),assess_paper_live_readiness(),assess_human_approval_readiness(),assess_execution_lockdown_readiness(),assess_audit_log_readiness(),assess_emergency_control_readiness(),assess_compliance_guardrail_readiness(),assess_system_stability_readiness()]
    steps.append({"name":"12_assessments","status":"ok"})
    sc=build_scorecard();steps.append({"name":"scorecard","status":"ok","detail":f"score={sc['phase101_scorecard']['score_pct']}%"})
    gg=build_go_no_go(sc);steps.append({"name":"go_no_go","status":"ok","detail":gg["phase101_go_no_go"]["decision"]})
    mr=build_markdown_report(sc,gg);steps.append({"name":"markdown_report","status":"ok"})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={
        "phase101_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),
            "assessment_only":True,"live_trading_enabled":False,"broker_integration_allowed":False,"order_creation_allowed":False,
            "domains_assessed":len(assessments),
            "domains_ready":sc["phase101_scorecard"]["domains_ready"],
            "domains_not_ready":sc["phase101_scorecard"]["domains_not_ready"],
            "overall_score":sc["phase101_scorecard"]["score_pct"],
            "overall_readiness":sc["phase101_scorecard"]["overall_readiness"],
            "go_no_go":gg["phase101_go_no_go"]["decision"],
            "critical_blockers":len(sc["phase101_scorecard"]["critical_blockers"]),
            "major_gaps":len(sc["phase101_scorecard"]["major_gaps"]),
            "go_live_trading":False,
            "steps":steps,
            "mock_used":False,"fixture_used":False,"raw_saved":False,
            "pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
        }
    }
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
