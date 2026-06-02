import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase115_config import load_config
from smr_phase115_domain_registry import build_domain_registry
from smr_phase115_candidate_loader import load_all_candidates
from smr_phase115_status_classifier import build_status_classifier
from smr_phase115_category_board import build_category_board
from smr_phase115_evidence_summary import build_evidence_summary
from smr_phase115_risk_summary import build_risk_summary
from smr_phase115_action_planner import build_action_planner
from smr_phase115_blocked_panel import build_blocked_panel
from smr_phase115_risk_catalyst_panel import build_risk_catalyst_panel
from smr_phase115_new_opportunity_board import build_new_opportunity_board
from smr_phase115_cannot_conclude_guard import run_candidate_board_guard
from smr_phase115_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    dom=build_domain_registry();steps.append({"name":"domain_registry","status":"ok"})
    cand=load_all_candidates();steps.append({"name":"candidate_loader","status":"ok","detail":f"total={cand['phase115_candidate_loader']['total']}"})
    cls=build_status_classifier();steps.append({"name":"classifier","status":"ok"})
    board=build_category_board();steps.append({"name":"board","status":"ok","detail":str(board['phase115_category_board']['section_counts'])})
    ev=build_evidence_summary();steps.append({"name":"evidence","status":"ok"})
    risk=build_risk_summary();steps.append({"name":"risk","status":"ok"})
    ap=build_action_planner();steps.append({"name":"actions","status":"ok","detail":f"total={ap['phase115_action_planner']['total']}"})
    bp=build_blocked_panel();steps.append({"name":"blocked_panel","status":"ok"})
    rp=build_risk_catalyst_panel();steps.append({"name":"risk_panel","status":"ok"})
    nb=build_new_opportunity_board();steps.append({"name":"new_opportunity","status":"ok"})
    guard=run_candidate_board_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase115_guard"]["overall"]})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={"phase115_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),"research_only":True,"candidates":cand["phase115_candidate_loader"]["total"],"sections":board["phase115_category_board"]["section_counts"],"owner_actions":ap["phase115_action_planner"]["total"],"guard":guard["phase115_guard"]["overall"],"violations":guard["phase115_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase115_backlog"]["next_phase_recommendation"],"steps":steps,"paper_order_created":0,"paper_trade_created":0,"paper_position_created":0,"paper_pnl_calculated":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
