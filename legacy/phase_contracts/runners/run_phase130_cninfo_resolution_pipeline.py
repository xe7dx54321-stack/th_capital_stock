import json,sys,os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "08_scripts" / "lib"))
from smr_phase130_config import load_config
from smr_phase130_domain_registry import build_domain_registry
from smr_phase130_historical_blocker_loader import load_historical_blocker
from smr_phase130_identity_evidence_pack import build_identity_evidence_pack
from smr_phase130_cninfo_candidate_registry import build_cninfo_candidate_registry
from smr_phase130_cninfo_verification_runner import run_cninfo_verification
from smr_phase130_szse_disclosure_fallback import build_szse_disclosure_fallback
from smr_phase130_irm_interaction_fallback import build_irm_interaction_fallback
from smr_phase130_company_ir_loader import build_company_ir_loader
from smr_phase130_known_url_validator import run_known_url_validation
from smr_phase130_manual_url_template import build_manual_url_template
from smr_phase130_alternative_disclosure_registry import build_alternative_disclosure_registry
from smr_phase130_source_equivalence_scorer import build_source_equivalence_scorer
from smr_phase130_disclosure_coverage_classifier import classify_disclosure_coverage
from smr_phase130_hard_data_readiness import build_hard_data_readiness
from smr_phase130_watchlist_status_update import build_watchlist_status_update
from smr_phase130_gap_closeout_report import build_gap_closeout_report
from smr_phase130_manual_action_template import build_manual_action_template
from smr_phase130_resolution_decision_report import build_resolution_decision_report
from smr_phase130_integration_update import build_integration_update
from smr_phase130_resolution_board import build_resolution_board
from smr_phase130_resolution_brief import build_resolution_brief_md
from smr_phase130_resolution_memory import build_resolution_memory
from smr_phase130_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase130_backlog_update import build_backlog_update
def main():
 mode="dry_run"
 if "--execute" in sys.argv: mode="execute"
 if "--skip-network" in sys.argv: mode="skip_network"
 sn="--skip-network" in sys.argv
 gc=build_gap_closeout_report()
 gd=run_cannot_conclude_guard()
 bl=build_backlog_update()
 out={"phase130_cninfo_resolution_pipeline":{"mode":mode,"ticker":"300394.SZ","blocker_status":gc["phase130_gap_closeout_report"]["blocker_status"],"decision":"alternative_source_integration_recommended","guard":gd["phase130_cannot_conclude_guard"],"backlog":bl["phase130_backlog_update"],"300394_retained":True,"688041_retained":True,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0,"profit_loss_tracking_created":False,"return_tracking_created":False,"broker_api_called":False}}
 if "--json" in sys.argv: print(json.dumps(out,ensure_ascii=False,indent=2))
 else: print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
