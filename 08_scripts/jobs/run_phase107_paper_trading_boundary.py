import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase107_config import load_config
from smr_phase107_paper_concept_registry import build_paper_concept_registry
from smr_phase107_paper_state_taxonomy import build_paper_state_taxonomy
from smr_phase107_paper_action_registry import build_paper_action_registry
from smr_phase107_paper_signal_boundary import build_paper_signal_boundary
from smr_phase107_paper_intent_boundary import build_paper_intent_boundary
from smr_phase107_paper_order_boundary import build_paper_order_boundary
from smr_phase107_paper_trade_boundary import build_paper_trade_boundary
from smr_phase107_paper_portfolio_boundary import build_paper_portfolio_boundary
from smr_phase107_paper_pnl_boundary import build_paper_pnl_boundary
from smr_phase107_paper_pre_paper_checklist import build_pre_paper_readiness_checklist
from smr_phase107_paper_boundary_dependency_matrix import build_paper_boundary_dependency_matrix
from smr_phase107_paper_no_order_simulation import run_paper_no_order_simulation
from smr_phase107_paper_violation_classifier import build_paper_violation_classifier
from smr_phase107_paper_audit_schema import build_paper_audit_schema
from smr_phase107_paper_boundary_scorecard import build_paper_boundary_scorecard
from smr_phase107_paper_boundary_report import build_paper_boundary_report
from smr_phase107_paper_cannot_conclude_guard import run_paper_guard
from smr_phase107_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    reg=build_paper_concept_registry();steps.append({"name":"concept_registry","status":"ok","detail":f"concepts={reg['phase107_paper_concept_registry']['total_concepts']}"})
    st=build_paper_state_taxonomy();steps.append({"name":"state_taxonomy","status":"ok","detail":st["phase107_paper_state_taxonomy"]["current_state"]})
    ar=build_paper_action_registry();steps.append({"name":"action_registry","status":"ok","detail":f"allowed={ar['phase107_paper_action_registry']['allowed']},forbidden={ar['phase107_paper_action_registry']['forbidden']}"})
    sb=build_paper_signal_boundary();steps.append({"name":"signal_boundary","status":"ok"})
    ib=build_paper_intent_boundary();steps.append({"name":"intent_boundary","status":"ok"})
    ob=build_paper_order_boundary();steps.append({"name":"order_boundary","status":"ok"})
    tb=build_paper_trade_boundary();steps.append({"name":"trade_boundary","status":"ok"})
    pb=build_paper_portfolio_boundary();steps.append({"name":"portfolio_boundary","status":"ok"})
    pnb=build_paper_pnl_boundary();steps.append({"name":"pnl_boundary","status":"ok"})
    cl=build_pre_paper_readiness_checklist();steps.append({"name":"checklist","status":"ok","detail":f"satisfied={cl['phase107_pre_paper_readiness_checklist']['items_satisfied']}/{cl['phase107_pre_paper_readiness_checklist']['total_items']}"})
    dm=build_paper_boundary_dependency_matrix();steps.append({"name":"dependency_matrix","status":"ok"})
    sim=run_paper_no_order_simulation();steps.append({"name":"no_order_simulation","status":"ok","detail":f"violations={sim['phase107_paper_no_order_simulation']['violations']}"})
    vc=build_paper_violation_classifier();steps.append({"name":"violation_classifier","status":"ok"})
    au=build_paper_audit_schema();steps.append({"name":"audit_schema","status":"ok"})
    sc=build_paper_boundary_scorecard();steps.append({"name":"scorecard","status":"ok","detail":f"ready_for_paper_execution={sc['phase107_paper_boundary_scorecard']['ready_for_paper_execution']}"})
    rpt=build_paper_boundary_report();steps.append({"name":"boundary_report","status":"ok"})
    guard=run_paper_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase107_guard"]["overall"]})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={
        "phase107_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),
            "assessment_only":True,"boundary_definition_only":True,"paper_trading_enabled":False,
            "paper_order_creation_allowed":False,"paper_trade_creation_allowed":False,
            "concepts_defined":reg["phase107_paper_concept_registry"]["total_concepts"],
            "current_state":st["phase107_paper_state_taxonomy"]["current_state"],
            "ready_for_paper_execution":False,"paper_trading_boundary_missing":"addressed",
            "paper_order_execution_missing":"unresolved","paper_trade_execution_missing":"unresolved",
            "guard":guard["phase107_guard"]["overall"],"violations":guard["phase107_guard"]["violations"],
            "steps":steps,
            "paper_order_created":False,"paper_trade_created":False,"paper_pnl_calculated":False,
            "mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,
            "pending_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
        }
    }
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
