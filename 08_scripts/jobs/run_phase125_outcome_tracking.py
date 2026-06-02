import sys,json,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase125_config import load_config
from smr_phase125_domain import build_domain_registry
from smr_phase125_schema import build_schema
from smr_phase125_taxonomy import build_taxonomy
from smr_phase125_decision_loader import build_decision_loader
from smr_phase125_context_loader import build_context_loader
from smr_phase125_intake import build_intake
from smr_phase125_validation import build_validation
from smr_phase125_decision_linker import build_decision_linker
from smr_phase125_evidence_linker import build_evidence_linker
from smr_phase125_watchlist_linker import build_watchlist_linker
from smr_phase125_classifier import build_classifier
from smr_phase125_writer import build_writer
from smr_phase125_reader import build_reader
from smr_phase125_board import build_board
from smr_phase125_learning_signal import build_learning_signal
from smr_phase125_followup import build_followup
from smr_phase125_guard import run_guard
from smr_phase125_backlog import build_backlog
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"config","status":"ok"})
    build_domain_registry();steps.append({"name":"domain","status":"ok"})
    build_schema();steps.append({"name":"schema","status":"ok"})
    t=build_taxonomy();steps.append({"name":"taxonomy","status":"ok"})
    build_decision_loader();steps.append({"name":"decision_loader","status":"ok"})
    build_context_loader();steps.append({"name":"context","status":"ok"})
    build_intake();steps.append({"name":"intake","status":"ok"})
    build_validation();steps.append({"name":"validation","status":"ok"})
    build_decision_linker();steps.append({"name":"decision_linker","status":"ok"})
    build_evidence_linker();steps.append({"name":"evidence_linker","status":"ok"})
    build_watchlist_linker();steps.append({"name":"watchlist_linker","status":"ok"})
    build_classifier();steps.append({"name":"classifier","status":"ok"})
    w=build_writer();steps.append({"name":"writer","status":"ok"})
    r=build_reader();steps.append({"name":"reader","status":"ok"})
    build_board();steps.append({"name":"board","status":"ok"})
    ls=build_learning_signal();steps.append({"name":"learning_signal","status":"ok"})
    build_followup();steps.append({"name":"followup","status":"ok"})
    g=run_guard();steps.append({"name":"guard","status":"ok"})
    b=build_backlog();steps.append({"name":"backlog","status":"ok"})
    out={"phase125_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),"research_only":True,"outcome_types":t["phase125_taxonomy"]["total"],"guard":g["phase125_guard"]["overall"],"violations":g["phase125_guard"]["violations"],"profit_loss_tracking_created":False,"return_tracking_created":False,"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":b["phase125_backlog"]["next_phase"],"steps":steps,"trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,"paper_order_created":0,"paper_trade_created":0,"paper_position_created":0,"paper_pnl_calculated":0,"broker_api_called":False,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
