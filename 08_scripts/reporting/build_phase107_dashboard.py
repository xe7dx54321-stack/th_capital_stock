import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase107_config import load_config
from smr_phase107_paper_concept_registry import build_paper_concept_registry
from smr_phase107_paper_state_taxonomy import build_paper_state_taxonomy
from smr_phase107_paper_action_registry import build_paper_action_registry
from smr_phase107_paper_pre_paper_checklist import build_pre_paper_readiness_checklist
from smr_phase107_paper_boundary_dependency_matrix import build_paper_boundary_dependency_matrix
from smr_phase107_paper_no_order_simulation import run_paper_no_order_simulation
from smr_phase107_paper_boundary_scorecard import build_paper_boundary_scorecard
from smr_phase107_paper_boundary_report import build_paper_boundary_report
from smr_phase107_paper_cannot_conclude_guard import run_paper_guard
from smr_phase107_backlog_update import build_backlog_update
def main():
    cfg=load_config();reg=build_paper_concept_registry();st=build_paper_state_taxonomy()
    ar=build_paper_action_registry();cl=build_pre_paper_readiness_checklist()
    dm=build_paper_boundary_dependency_matrix();sim=run_paper_no_order_simulation()
    sc=build_paper_boundary_scorecard();rpt=build_paper_boundary_report()
    guard=run_paper_guard();bl=build_backlog_update()
    summary={
        "phase":"phase107","generated_at":datetime.now().isoformat(),
        "assessment_only":cfg["paper_trading"]["assessment_only"],
        "boundary_definition_only":cfg["paper_trading"]["boundary_definition_only"],
        "paper_trading_enabled":cfg["paper_trading"]["paper_trading_enabled"],
        "paper_order_creation_allowed":cfg["paper_trading"]["paper_order_creation_allowed"],
        "paper_trade_creation_allowed":cfg["paper_trading"]["paper_trade_creation_allowed"],
        "scorecard":sc["phase107_paper_boundary_scorecard"],
        "guard":guard["phase107_guard"]["overall"],"violations":guard["phase107_guard"]["violations"],
        "paper_trading_boundary_missing":"addressed",
        "paper_order_execution_missing":"unresolved","paper_trade_execution_missing":"unresolved",
        "ready_for_paper_execution":False,
        "blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],
        "paper_order_created":False,"paper_trade_created":False,"paper_pnl_calculated":False,
        "mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,
        "pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
