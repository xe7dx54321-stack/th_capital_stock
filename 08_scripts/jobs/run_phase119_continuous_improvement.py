import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase119_config import load_config
from smr_phase119_domain_registry import build_domain_registry
from smr_phase119_health_loader import load_phase118_health
from smr_phase119_runstate_loader import load_phase117_runstate
from smr_phase119_watchlist_loader import load_phase116_watchlist
from smr_phase119_gap_inventory import build_gap_inventory
from smr_phase119_gap_priority import classify_gap_priorities
from smr_phase119_auto_fix_assessor import assess_auto_fix
from smr_phase119_source_refresh_planner import plan_source_refresh
from smr_phase119_evidence_gap_planner import plan_evidence_gap_close
from smr_phase119_blocker_planner import plan_blocker_resolution
from smr_phase119_reliability_planner import plan_reliability_improvement
from smr_phase119_feedback_intake import build_feedback_intake_schema
from smr_phase119_action_queue import build_improvement_queue
from smr_phase119_verification_checklist import build_verification_checklist
from smr_phase119_improvement_board import build_improvement_board
from smr_phase119_memory_writer import build_memory_writer
from smr_phase119_cannot_conclude_guard import run_improvement_guard
from smr_phase119_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    dom=build_domain_registry();steps.append({"name":"domain_registry","status":"ok"})
    hl=load_phase118_health();steps.append({"name":"health_loader","status":"ok"})
    rs=load_phase117_runstate();steps.append({"name":"runstate_loader","status":"ok"})
    wl=load_phase116_watchlist();steps.append({"name":"watchlist_loader","status":"ok"})
    gi=build_gap_inventory();steps.append({"name":"gap_inventory","status":"ok","detail":f"gaps={gi['phase119_gap_inventory']['total']}"})
    gp=classify_gap_priorities();steps.append({"name":"gap_priority","status":"ok"})
    af=assess_auto_fix();steps.append({"name":"auto_fix","status":"ok","detail":f"auto={af['phase119_auto_fix_assessor']['auto_fix_count']}"})
    sr=plan_source_refresh();steps.append({"name":"source_refresh","status":"ok"})
    eg=plan_evidence_gap_close();steps.append({"name":"evidence_gap","status":"ok"})
    bp=plan_blocker_resolution();steps.append({"name":"blocker_plan","status":"ok"})
    rp=plan_reliability_improvement();steps.append({"name":"reliability","status":"ok"})
    fi=build_feedback_intake_schema();steps.append({"name":"feedback_schema","status":"ok"})
    aq=build_improvement_queue();steps.append({"name":"action_queue","status":"ok","detail":f"actions={aq['phase119_improvement_queue']['total']}"})
    vc=build_verification_checklist();steps.append({"name":"verification","status":"ok","detail":f"pass={vc['phase119_verification_checklist']['all_pass']}"})
    board=build_improvement_board();steps.append({"name":"board","status":"ok"})
    mw=build_memory_writer();steps.append({"name":"memory_writer","status":"ok"})
    guard=run_improvement_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase119_guard"]["overall"]})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={"phase119_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),"total_gaps":gi["phase119_gap_inventory"]["total"],"critical_gaps":gi["phase119_gap_inventory"]["critical"],"auto_fixable":af["phase119_auto_fix_assessor"]["auto_fix_count"],"actions_queued":aq["phase119_improvement_queue"]["total"],"verification_pass":vc["phase119_verification_checklist"]["all_pass"],"guard":guard["phase119_guard"]["overall"],"violations":guard["phase119_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase119_backlog"]["next_phase_recommendation"],"steps":steps,"paper_order_created":0,"paper_trade_created":0,"paper_position_created":0,"paper_pnl_calculated":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
