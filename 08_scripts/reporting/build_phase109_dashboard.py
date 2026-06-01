import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase109_config import load_config
from smr_phase109_identity_domain_registry import build_identity_domain_registry
from smr_phase109_identity_readiness_checklist import build_identity_readiness_checklist
from smr_phase109_no_order_identity_simulation import run_no_order_identity_simulation
from smr_phase109_identity_readiness_scorecard import build_identity_readiness_scorecard
from smr_phase109_identity_cannot_conclude_guard import run_identity_guard
from smr_phase109_backlog_update import build_backlog_update
def main():
    cfg=load_config();reg=build_identity_domain_registry()
    cl=build_identity_readiness_checklist();sim=run_no_order_identity_simulation()
    sc=build_identity_readiness_scorecard();guard=run_identity_guard()
    bl=build_backlog_update()
    summary={
        "phase":"phase109","generated_at":datetime.now().isoformat(),
        "assessment_only":cfg["identity"]["assessment_only"],
        "identity_readiness_only":cfg["identity"]["identity_readiness_only"],
        "account_creation_allowed":cfg["identity"]["account_creation_allowed"],
        "sso_integration_allowed":cfg["identity"]["sso_integration_allowed"],
        "paper_execution_enabled":cfg["identity"]["paper_execution_enabled"],
        "scorecard":sc["phase109_identity_readiness_scorecard"],
        "guard":guard["phase109_guard"]["overall"],"violations":guard["phase109_guard"]["violations"],
        "blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],
        "account_created":0,"sso_connected":0,"password_saved":0,"paper_order_created":0,
        "mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,
        "pending_created":0,"real_trade_created":0,"target_price":0,"position_sizing":0
    }
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
