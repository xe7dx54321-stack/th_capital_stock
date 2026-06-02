import sys,json,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase123_config import load_config
from smr_phase123_domain_registry import build_domain_registry
from smr_phase123_feedback_schema import build_feedback_schema
from smr_phase123_feedback_intake import build_feedback_intake
from smr_phase123_feedback_validation import build_feedback_validation
from smr_phase123_feedback_classifier import build_feedback_classifier
from smr_phase123_feedback_entity_linker import build_feedback_entity_linker
from smr_phase123_feedback_memory_writer import build_feedback_memory_writer
from smr_phase123_feedback_memory_reader import build_feedback_memory_reader
from smr_phase123_feedback_impact_scorer import build_feedback_impact_scorer
from smr_phase123_opp_adapter import build_opp_adapter
from smr_phase123_brief_adapter import build_brief_adapter
from smr_phase123_source_adapter import build_source_adapter
from smr_phase123_watchlist_adapter import build_watchlist_adapter
from smr_phase123_feedback_action_planner import build_feedback_action_planner
from smr_phase123_feedback_board import build_feedback_board
from smr_phase123_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase123_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"config","status":"ok"})
    build_domain_registry();steps.append({"name":"domain","status":"ok"})
    build_feedback_schema();steps.append({"name":"schema","status":"ok"})
    build_feedback_intake();steps.append({"name":"intake","status":"ok"})
    build_feedback_validation();steps.append({"name":"validation","status":"ok"})
    clf=build_feedback_classifier();steps.append({"name":"classifier","status":"ok"})
    build_feedback_entity_linker();steps.append({"name":"linker","status":"ok"})
    w=build_feedback_memory_writer();steps.append({"name":"writer","status":"ok"})
    r=build_feedback_memory_reader();steps.append({"name":"reader","status":"ok"})
    build_feedback_impact_scorer();steps.append({"name":"impact","status":"ok"})
    build_opp_adapter();steps.append({"name":"opp_adapter","status":"ok"})
    build_brief_adapter();steps.append({"name":"brief_adapter","status":"ok"})
    build_source_adapter();steps.append({"name":"source_adapter","status":"ok"})
    build_watchlist_adapter();steps.append({"name":"watchlist_adapter","status":"ok"})
    ap=build_feedback_action_planner();steps.append({"name":"action_planner","status":"ok"})
    build_feedback_board();steps.append({"name":"board","status":"ok"})
    grd=run_cannot_conclude_guard();steps.append({"name":"guard","status":"ok"})
    blg=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={"phase123_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),"research_only":True,"feedback_types":clf["phase123_feedback_classifier"]["feedback_types"],"memory_path_ignored":True,"guard":grd["phase123_guard"]["overall"],"violations":grd["phase123_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":blg["phase123_backlog"]["next_phase"],"steps":steps,"trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,"paper_order_created":0,"paper_trade_created":0,"paper_position_created":0,"paper_pnl_calculated":0,"broker_api_called":False,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
