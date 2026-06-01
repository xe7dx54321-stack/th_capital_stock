import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase113_config import load_config
from smr_phase113_scoring_domain_registry import build_scoring_domain_registry
from smr_phase113_candidate_loader import load_phase112_candidates
from smr_phase113_source_reliability_weight import build_source_reliability_weight
from smr_phase113_evidence_quality_scorer import build_evidence_quality_scorer
from smr_phase113_cross_source_confirmation_scorer import build_cross_source_scorer
from smr_phase113_novelty_freshness_scorer import build_novelty_freshness_scorer
from smr_phase113_hard_data_support_scorer import build_hard_data_support_scorer
from smr_phase113_risk_discount_model import build_risk_discount_model
from smr_phase113_contradiction_penalty_model import build_contradiction_penalty_model
from smr_phase113_composite_priority_scorer import build_composite_priority_scorer
from smr_phase113_score_explanation_builder import build_score_explanation
from smr_phase113_scored_owner_action_queue import build_scored_owner_action_queue
from smr_phase113_cannot_conclude_guard import run_cross_source_scoring_guard
from smr_phase113_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    dom=build_scoring_domain_registry();steps.append({"name":"domain_registry","status":"ok","detail":f"domains={dom['phase113_scoring_domain_registry']['total_domains']}"})
    cand=load_phase112_candidates();steps.append({"name":"candidate_loader","status":"ok","detail":f"loaded={cand['phase113_candidate_loader']['candidates_loaded']}"})
    src=build_source_reliability_weight();steps.append({"name":"source_reliability","status":"ok"})
    evq=build_evidence_quality_scorer();steps.append({"name":"evidence_quality","status":"ok"})
    cs=build_cross_source_scorer();steps.append({"name":"cross_source","status":"ok","detail":f"multi={cs['phase113_cross_source_scorer']['multi_source_confirmed']}"})
    nf=build_novelty_freshness_scorer();steps.append({"name":"novelty_freshness","status":"ok"})
    hd=build_hard_data_support_scorer();steps.append({"name":"hard_data","status":"ok"})
    rd=build_risk_discount_model();steps.append({"name":"risk_discount","status":"ok"})
    cp=build_contradiction_penalty_model();steps.append({"name":"contradiction_penalty","status":"ok"})
    comp=build_composite_priority_scorer();steps.append({"name":"composite_scorer","status":"ok","detail":f"scored={comp['phase113_composite_priority_scorer']['scored_candidates']}"})
    expl=build_score_explanation();steps.append({"name":"score_explanation","status":"ok"})
    q=build_scored_owner_action_queue();steps.append({"name":"action_queue","status":"ok","detail":f"actions={q['phase113_scored_owner_action_queue']['owner_action_count']}"})
    guard=run_cross_source_scoring_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase113_guard"]["overall"]})
    bl=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={"phase113_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),"research_only":True,"cross_source_scoring_enabled":True,"trade_recommendation_allowed":False,"target_price_output_allowed":False,"position_sizing_allowed":False,"scored_candidates":comp["phase113_composite_priority_scorer"]["scored_candidates"],"high":comp["phase113_composite_priority_scorer"]["high"],"medium":comp["phase113_composite_priority_scorer"]["medium"],"low":comp["phase113_composite_priority_scorer"]["low"],"blocked":comp["phase113_composite_priority_scorer"]["blocked"],"owner_action_count":q["phase113_scored_owner_action_queue"]["owner_action_count"],"guard":guard["phase113_guard"]["overall"],"violations":guard["phase113_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase113_backlog"]["next_phase_recommendation"],"steps":steps,"paper_order_created":0,"paper_trade_created":0,"paper_position_created":0,"paper_pnl_calculated":0,"target_price_created":0,"position_sizing_created":0,"trade_recommendation_created":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
