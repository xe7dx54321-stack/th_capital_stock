import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase108_config import load_config
from smr_phase108_readiness_domain_registry import build_readiness_domain_registry
from smr_phase108_pre_paper_checklist import build_pre_paper_checklist
from smr_phase108_safety_gate import run_safety_gate
from smr_phase108_disabled_state_verifier import run_disabled_state_verifier
from smr_phase108_dry_run_simulation import run_dry_run_simulation
from smr_phase108_readiness_scorecard import build_readiness_scorecard
from smr_phase108_readiness_report import build_readiness_report
from smr_phase108_cannot_conclude_guard import run_guard
from smr_phase108_backlog_update import build_backlog_update
def main():
    cfg=load_config();reg=build_readiness_domain_registry();cl=build_pre_paper_checklist()
    sg=run_safety_gate();dv=run_disabled_state_verifier();sim=run_dry_run_simulation()
    sc=build_readiness_scorecard();rpt=build_readiness_report()
    guard=run_guard();bl=build_backlog_update()
    summary={
        "phase":"phase108","generated_at":datetime.now().isoformat(),
        "assessment_only":cfg["paper_execution"]["assessment_only"],
        "readiness_only":cfg["paper_execution"]["readiness_only"],
        "paper_execution_enabled":cfg["paper_execution"]["paper_execution_enabled"],
        "paper_order_creation_allowed":cfg["paper_execution"]["paper_order_creation_allowed"],
        "paper_trade_creation_allowed":cfg["paper_execution"]["paper_trade_creation_allowed"],
        "scorecard":sc["phase108_readiness_scorecard"],
        "safety_gate":sg["phase108_safety_gate"]["overall"],
        "all_disabled":dv["phase108_disabled_state_verifier"]["all_disabled"],
        "guard":guard["phase108_guard"]["overall"],"violations":guard["phase108_guard"]["violations"],
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
