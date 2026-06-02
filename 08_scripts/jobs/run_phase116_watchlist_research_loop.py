import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase116_config import load_config
from smr_phase116_domain_registry import build_domain_registry
from smr_phase116_universe_loader import load_watchlist_universe
from smr_phase115_board_loader import load_phase115_candidate_board
from smr_phase116_state_schema import build_research_state_schema
from smr_phase116_state_classifier import classify_watchlist_states
from smr_phase116_candidate_mapper import map_candidates_to_watchlist
from smr_phase116_evidence_refresh import build_evidence_refresh
from smr_phase116_thesis_summary import build_thesis_summary
from smr_phase116_risk_summary import build_risk_summary
from smr_phase116_action_planner import build_action_planner
from smr_phase116_status_transition import build_status_transition
from smr_phase116_research_board import build_research_board
from smr_phase116_memory_writer import build_memory_writer
from smr_phase116_cannot_conclude_guard import run_watchlist_guard
from smr_phase116_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    dom=build_domain_registry();steps.append({"name":"domain_registry","status":"ok"})
    uni=load_watchlist_universe();steps.append({"name":"universe","status":"ok","detail":str(uni["phase116_universe"]["states"])})
    brd=load_phase115_candidate_board();steps.append({"name":"board_loader","status":"ok"})
    schema=build_research_state_schema();steps.append({"name":"state_schema","status":"ok"})
    cls=classify_watchlist_states();steps.append({"name":"classifier","status":"ok"})
    mp=map_candidates_to_watchlist();steps.append({"name":"mapper","status":"ok"})
    ev=build_evidence_refresh();steps.append({"name":"evidence","status":"ok","detail":f"needs_refresh={ev['phase116_evidence_refresh']['needs_refresh']}"})
    th=build_thesis_summary();steps.append({"name":"thesis","status":"ok","detail":f"strengthened={th['phase116_thesis_summary']['strengthened']}"})
    risk=build_risk_summary();steps.append({"name":"risk","status":"ok"})
    ap=build_action_planner();steps.append({"name":"actions","status":"ok","detail":f"total={ap['phase116_action_planner']['total']}"})
    st=build_status_transition();steps.append({"name":"transitions","status":"ok"})
    board=build_research_board();steps.append({"name":"research_board","status":"ok"})
    mem=build_memory_writer();steps.append({"name":"memory_writer","status":"ok"})
    guard=run_watchlist_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase116_guard"]["overall"]})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={"phase116_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),"research_only":True,"tickers":board["phase116_research_board"]["total"],"sections":board["phase116_research_board"]["section_counts"],"owner_actions":ap["phase116_action_planner"]["total"],"guard":guard["phase116_guard"]["overall"],"violations":guard["phase116_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase116_backlog"]["next_phase_recommendation"],"steps":steps,"paper_order_created":0,"paper_trade_created":0,"paper_position_created":0,"paper_pnl_calculated":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
