import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase108_config import load_config
from smr_phase108_readiness_domain_registry import build_readiness_domain_registry
from smr_phase108_pre_paper_checklist import build_pre_paper_checklist
from smr_phase108_paper_order_schema_review import build_paper_order_schema_review
from smr_phase108_paper_trade_schema_review import build_paper_trade_schema_review
from smr_phase108_paper_portfolio_schema_review import build_paper_portfolio_schema_review
from smr_phase108_paper_pnl_policy_readiness import build_paper_pnl_policy_readiness
from smr_phase108_paper_sizing_policy_readiness import build_paper_sizing_policy_readiness
from smr_phase108_operator_identity_dependency import build_operator_identity_dependency
from smr_phase108_approval_dependency import build_approval_dependency
from smr_phase108_risk_dependency import build_risk_dependency
from smr_phase108_kill_switch_dependency import build_kill_switch_dependency
from smr_phase108_audit_readiness import build_audit_readiness
from smr_phase108_safety_gate import run_safety_gate
from smr_phase108_disabled_state_verifier import run_disabled_state_verifier
from smr_phase108_dry_run_simulation import run_dry_run_simulation
from smr_phase108_violation_classifier import build_violation_classifier
from smr_phase108_readiness_scorecard import build_readiness_scorecard
from smr_phase108_readiness_report import build_readiness_report
from smr_phase108_cannot_conclude_guard import run_guard
from smr_phase108_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    reg=build_readiness_domain_registry();steps.append({"name":"domain_registry","status":"ok","detail":f"domains={reg['phase108_readiness_domain_registry']['total_domains']}"})
    cl=build_pre_paper_checklist();steps.append({"name":"checklist","status":"ok","detail":f"satisfied={cl['phase108_pre_paper_checklist']['items_satisfied']}/{cl['phase108_pre_paper_checklist']['items_total']}"})
    osr=build_paper_order_schema_review();steps.append({"name":"order_schema_review","status":"ok"})
    tsr=build_paper_trade_schema_review();steps.append({"name":"trade_schema_review","status":"ok"})
    psr=build_paper_portfolio_schema_review();steps.append({"name":"portfolio_schema_review","status":"ok"})
    pp=build_paper_pnl_policy_readiness();steps.append({"name":"pnl_policy","status":"ok","detail":pp["phase108_paper_pnl_policy_readiness"]["readiness_status"]})
    sp=build_paper_sizing_policy_readiness();steps.append({"name":"sizing_policy","status":"ok","detail":sp["phase108_paper_sizing_policy_readiness"]["readiness_status"]})
    oi=build_operator_identity_dependency();steps.append({"name":"operator_identity","status":"ok","detail":oi["phase108_operator_identity_dependency"]["status"]})
    ap=build_approval_dependency();steps.append({"name":"approval","status":"ok","detail":ap["phase108_approval_dependency"]["status"]})
    rk=build_risk_dependency();steps.append({"name":"risk","status":"ok","detail":rk["phase108_risk_dependency"]["status"]})
    ks=build_kill_switch_dependency();steps.append({"name":"kill_switch","status":"ok","detail":ks["phase108_kill_switch_dependency"]["status"]})
    au=build_audit_readiness();steps.append({"name":"audit","status":"ok"})
    sg=run_safety_gate();steps.append({"name":"safety_gate","status":"ok","detail":sg["phase108_safety_gate"]["overall"]})
    dv=run_disabled_state_verifier();steps.append({"name":"disabled_verifier","status":"ok","detail":f"all_disabled={dv['phase108_disabled_state_verifier']['all_disabled']}"})
    sim=run_dry_run_simulation();steps.append({"name":"dry_run_simulation","status":"ok","detail":f"violations={sim['phase108_dry_run_simulation']['violations']}"})
    vc=build_violation_classifier();steps.append({"name":"violation_classifier","status":"ok"})
    sc=build_readiness_scorecard();steps.append({"name":"scorecard","status":"ok","detail":f"ready_for_execution={sc['phase108_readiness_scorecard']['ready_for_paper_execution']}"})
    rpt=build_readiness_report();steps.append({"name":"readiness_report","status":"ok"})
    guard=run_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase108_guard"]["overall"]})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={
        "phase108_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),
            "assessment_only":True,"readiness_only":True,"paper_execution_enabled":False,
            "paper_order_creation_allowed":False,"paper_trade_creation_allowed":False,
            "domains_assessed":reg["phase108_readiness_domain_registry"]["total_domains"],
            "checklist_satisfied":cl["phase108_pre_paper_checklist"]["items_satisfied"],
            "checklist_total":cl["phase108_pre_paper_checklist"]["items_total"],
            "ready_for_paper_execution":False,
            "safety_gate":sg["phase108_safety_gate"]["overall"],
            "all_disabled":dv["phase108_disabled_state_verifier"]["all_disabled"],
            "guard":guard["phase108_guard"]["overall"],"violations":guard["phase108_guard"]["violations"],
            "steps":steps,
            "paper_order_created":False,"paper_trade_created":False,"paper_pnl_calculated":False,
            "mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,
            "pending_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
        }
    }
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
