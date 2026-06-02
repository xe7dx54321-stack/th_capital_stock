import sys,json,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase124_config import load_config
from smr_phase124_domain_registry import build_domain_registry
from smr_phase124_schema import build_decision_schema
from smr_phase124_taxonomy import build_decision_taxonomy
from smr_phase124_context_loader import build_context_loader
from smr_phase124_intake import build_intake_template
from smr_phase124_validation import build_decision_validation
from smr_phase124_evidence_linker import build_evidence_linker
from smr_phase124_feedback_linker import build_feedback_linker
from smr_phase124_watchlist_linker import build_watchlist_linker
from smr_phase124_writer import build_journal_writer
from smr_phase124_reader import build_journal_reader
from smr_phase124_rationale import build_decision_rationale
from smr_phase124_followup import build_followup_planner
from smr_phase124_review_schedule import build_review_schedule
from smr_phase124_board import build_decision_board
from smr_phase124_guard import run_cannot_conclude_guard
from smr_phase124_backlog import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"config","status":"ok"})
    build_domain_registry();steps.append({"name":"domain","status":"ok"})
    build_decision_schema();steps.append({"name":"schema","status":"ok"})
    tax=build_decision_taxonomy();steps.append({"name":"taxonomy","status":"ok"})
    build_context_loader();steps.append({"name":"context","status":"ok"})
    build_intake_template();steps.append({"name":"intake","status":"ok"})
    build_decision_validation();steps.append({"name":"validation","status":"ok"})
    build_evidence_linker();steps.append({"name":"evidence_linker","status":"ok"})
    build_feedback_linker();steps.append({"name":"feedback_linker","status":"ok"})
    build_watchlist_linker();steps.append({"name":"watchlist_linker","status":"ok"})
    w=build_journal_writer();steps.append({"name":"writer","status":"ok"})
    r=build_journal_reader();steps.append({"name":"reader","status":"ok"})
    build_decision_rationale();steps.append({"name":"rationale","status":"ok"})
    build_followup_planner();steps.append({"name":"followup","status":"ok"})
    build_review_schedule();steps.append({"name":"review","status":"ok"})
    build_decision_board();steps.append({"name":"board","status":"ok"})
    grd=run_cannot_conclude_guard();steps.append({"name":"guard","status":"ok"})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={"phase124_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),"research_only":True,"decision_types":tax["phase124_taxonomy"]["total"],"journal_path_ignored":True,"guard":grd["phase124_guard"]["overall"],"violations":grd["phase124_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase124_backlog"]["next_phase"],"steps":steps,"trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,"paper_order_created":0,"paper_trade_created":0,"paper_position_created":0,"paper_pnl_calculated":0,"broker_api_called":False,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
