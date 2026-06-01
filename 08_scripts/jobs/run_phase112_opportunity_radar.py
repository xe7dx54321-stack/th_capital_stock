import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase112_config import load_config
from smr_phase112_opportunity_source_registry import build_opportunity_source_registry
from smr_phase112_opportunity_universe_loader import build_opportunity_universe
from smr_phase112_signal_taxonomy import build_radar_signal_taxonomy
from smr_phase112_signal_ingestion_adapter import build_signal_ingestion_report
from smr_phase112_candidate_builder import build_opportunity_candidate_pool
from smr_phase112_evidence_linkage import build_evidence_linkage
from smr_phase112_novelty_change_detector import build_novelty_change_report
from smr_phase112_signal_strength_classifier import build_signal_strength_report
from smr_phase112_research_risk_gate import build_research_risk_gate
from smr_phase112_opportunity_ranking import build_opportunity_ranking
from smr_phase112_owner_action_queue import build_owner_action_queue
from smr_phase112_cannot_conclude_guard import run_opportunity_cannot_conclude_guard
from smr_phase112_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    src=build_opportunity_source_registry();steps.append({"name":"source_registry","status":"ok","detail":f"sources={src['phase112_opportunity_source_registry']['active_sources']}"})
    uni=build_opportunity_universe();steps.append({"name":"universe","status":"ok","detail":f"radar_enabled={uni['phase112_opportunity_universe']['radar_enabled']}"})
    tax=build_radar_signal_taxonomy();steps.append({"name":"signal_taxonomy","status":"ok","detail":f"signals={tax['phase112_signal_taxonomy']['total_signals']}"})
    sig=build_signal_ingestion_report();steps.append({"name":"signal_ingestion","status":"ok","detail":f"signals={sig['phase112_signal_ingestion']['signals_loaded']}"})
    pool=build_opportunity_candidate_pool();steps.append({"name":"candidate_pool","status":"ok","detail":f"candidates={pool['phase112_opportunity_candidate_pool']['candidate_count']}"})
    ev=build_evidence_linkage();steps.append({"name":"evidence_linkage","status":"ok","detail":f"linkages={ev['phase112_evidence_linkage']['total_linkages']}"})
    nov=build_novelty_change_report();steps.append({"name":"novelty_detector","status":"ok","detail":f"new={nov['phase112_novelty_change']['new_signals']}"})
    stre=build_signal_strength_report();steps.append({"name":"strength_classifier","status":"ok","detail":f"strong={stre['phase112_signal_strength']['strong']}"})
    risk=build_research_risk_gate();steps.append({"name":"risk_gate","status":"ok","detail":f"high_risk={risk['phase112_research_risk_gate']['high_risk']}"})
    rank=build_opportunity_ranking();steps.append({"name":"ranking","status":"ok","detail":f"ranked={rank['phase112_opportunity_ranking']['total_ranked']}"})
    q=build_owner_action_queue();steps.append({"name":"action_queue","status":"ok","detail":f"actions={q['phase112_owner_action_queue']['owner_action_count']}"})
    guard=run_opportunity_cannot_conclude_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase112_guard"]["overall"]})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={"phase112_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),"research_only":True,"opportunity_discovery_mode":True,"trade_recommendation_allowed":False,"target_price_output_allowed":False,"position_sizing_allowed":False,"paper_execution_enabled":False,"live_trading_enabled":False,"active_sources":src["phase112_opportunity_source_registry"]["active_sources"],"signals_loaded":sig["phase112_signal_ingestion"]["signals_loaded"],"candidate_count":pool["phase112_opportunity_candidate_pool"]["candidate_count"],"blocked_candidates":pool["phase112_opportunity_candidate_pool"]["blocked_count"],"owner_action_count":q["phase112_owner_action_queue"]["owner_action_count"],"guard":guard["phase112_guard"]["overall"],"violations":guard["phase112_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":"phase113_cross_source_opportunity_scoring","steps":steps,"paper_order_created":0,"paper_trade_created":0,"paper_position_created":0,"paper_pnl_calculated":0,"target_price_created":0,"position_sizing_created":0,"trade_recommendation_created":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
