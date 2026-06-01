import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase110_config import load_config
from smr_phase110_assignment_domain_registry import build_assignment_domain_registry
from smr_phase110_role_assignment_matrix import build_role_assignment_matrix
from smr_phase110_manual_assignment_checklist import build_manual_assignment_checklist
from smr_phase110_no_order_assignment_simulation import run_no_order_assignment_simulation
from smr_phase110_assignment_readiness_scorecard import build_assignment_scorecard
from smr_phase110_assignment_cannot_conclude_guard import run_assignment_guard
from smr_phase110_backlog_update import build_backlog_update
def main():
    cfg=load_config();reg=build_assignment_domain_registry();rm=build_role_assignment_matrix()
    cl=build_manual_assignment_checklist();sim=run_no_order_assignment_simulation()
    sc=build_assignment_scorecard();guard=run_assignment_guard();bl=build_backlog_update()
    summary={"phase":"phase110","generated_at":datetime.now().isoformat(),"assessment_only":cfg["assignment"]["assessment_only"],"manual_assignment_only":cfg["assignment"]["manual_assignment_only"],"auto_assignment_allowed":cfg["assignment"]["auto_assignment_allowed"],"account_creation_allowed":cfg["assignment"]["account_creation_allowed"],"paper_execution_enabled":cfg["assignment"]["paper_execution_enabled"],"scorecard":sc["phase110_assignment_scorecard"],"guard":guard["phase110_guard"]["overall"],"violations":guard["phase110_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"real_operators_assigned":0,"account_created":0,"sso_connected":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0}
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
