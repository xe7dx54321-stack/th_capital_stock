import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase114_config import load_config
from smr_phase114_catalyst_domain_registry import build_catalyst_domain_registry
from smr_phase114_candidate_loader import load_phase113_scored_candidates
from smr_phase114_catalyst_taxonomy import build_catalyst_taxonomy
from smr_phase114_inflection_signal_taxonomy import build_inflection_signal_taxonomy
from smr_phase114_catalyst_evidence_mapper import build_catalyst_evidence_mapper
from smr_phase114_expectation_change_detector import build_expectation_change_detector
from smr_phase114_thesis_change_detector import build_thesis_change_detector
from smr_phase114_catalyst_timing_classifier import build_catalyst_timing_classifier
from smr_phase114_catalyst_confidence_scorer import build_catalyst_confidence_scorer
from smr_phase114_catalyst_risk_gate import build_catalyst_risk_gate
from smr_phase114_inflection_explanation_builder import build_inflection_explanation
from smr_phase114_catalyst_action_queue import build_catalyst_action_queue
from smr_phase114_cannot_conclude_guard import run_catalyst_guard
from smr_phase114_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    dom=build_catalyst_domain_registry();steps.append({"name":"domain_registry","status":"ok","detail":f"domains={dom['phase114_catalyst_domain_registry']['total_domains']}"})
    cand=load_phase113_scored_candidates();steps.append({"name":"candidate_loader","status":"ok","detail":f"loaded={cand['phase114_candidate_loader']['candidates_loaded']}"})
    tax=build_catalyst_taxonomy();steps.append({"name":"catalyst_taxonomy","status":"ok","detail":f"types={tax['phase114_catalyst_taxonomy']['total_types']}"})
    inf=build_inflection_signal_taxonomy();steps.append({"name":"inflection_taxonomy","status":"ok"})
    ev=build_catalyst_evidence_mapper();steps.append({"name":"evidence_mapper","status":"ok","detail":f"catalysts={ev['phase114_catalyst_evidence_mapper']['catalysts_found']}"})
    exp=build_expectation_change_detector();steps.append({"name":"expectation_change","status":"ok","detail":f"sig={exp['phase114_expectation_change_detector']['significant_changes']}"})
    th=build_thesis_change_detector();steps.append({"name":"thesis_change","status":"ok","detail":f"strengthened={th['phase114_thesis_change_detector']['strengthened']}"})
    tm=build_catalyst_timing_classifier();steps.append({"name":"timing","status":"ok","detail":f"immediate={tm['phase114_catalyst_timing_classifier']['immediate']}"})
    cf=build_catalyst_confidence_scorer();steps.append({"name":"confidence","status":"ok","detail":f"high={cf['phase114_catalyst_confidence_scorer']['high_confidence']}"})
    rk=build_catalyst_risk_gate();steps.append({"name":"risk_gate","status":"ok"})
    expl=build_inflection_explanation();steps.append({"name":"explanation","status":"ok"})
    q=build_catalyst_action_queue();steps.append({"name":"action_queue","status":"ok","detail":f"actions={q['phase114_catalyst_action_queue']['total']}"})
    guard=run_catalyst_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase114_guard"]["overall"]})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={"phase114_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),"research_only":True,"catalyst_detection_enabled":True,"trade_recommendation_allowed":False,"target_price_output_allowed":False,"catalysts_found":ev["phase114_catalyst_evidence_mapper"]["catalysts_found"],"high_confidence":cf["phase114_catalyst_confidence_scorer"]["high_confidence"],"immediate_actions":tm["phase114_catalyst_timing_classifier"]["immediate"],"owner_actions":q["phase114_catalyst_action_queue"]["total"],"guard":guard["phase114_guard"]["overall"],"violations":guard["phase114_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase114_backlog"]["next_phase_recommendation"],"steps":steps,"paper_order_created":0,"paper_trade_created":0,"paper_position_created":0,"paper_pnl_calculated":0,"target_price_created":0,"position_sizing_created":0,"trade_recommendation_created":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
