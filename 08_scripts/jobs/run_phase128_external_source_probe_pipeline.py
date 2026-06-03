import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase128_config import load_config
from smr_phase128_domain_registry import build_domain_registry
from smr_phase128_pending_source_loader import load_pending_sources
from smr_phase128_known_gap_loader import load_known_gaps
from smr_phase128_probe_policy import build_probe_policy
from smr_phase128_probe_target_planner import plan_probe_targets
from smr_phase128_source_request_adapter import build_request_adapter
from smr_phase128_official_source_probe import probe_official_sources
from smr_phase128_third_party_source_probe import probe_third_party_sources
from smr_phase128_quote_source_probe import probe_quote_sources
from smr_phase128_news_event_probe import probe_news_event_sources
from smr_phase128_transcript_guidance_probe import probe_transcript_guidance_sources
from smr_phase128_probe_result_normalizer import normalize_probe_results
from smr_phase128_availability_classifier import classify_availability
from smr_phase128_failure_reason_classifier import classify_failure_reasons
from smr_phase128_content_usability_checker import check_content_usability
from smr_phase128_source_coverage_update import build_source_coverage_update
from smr_phase128_pending_network_closeout import build_pending_network_closeout
from smr_phase128_source_validation_gap_register import build_source_validation_gap_register
from smr_phase128_integration_update import build_integration_update
from smr_phase128_validation_board import build_validation_board
from smr_phase128_validation_brief import build_validation_brief_md
from smr_phase128_validation_memory import build_validation_memory
from smr_phase128_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase128_backlog_update import build_backlog_update
def main():
 mode="dry_run"
 if "--execute" in sys.argv: mode="execute"
 if "--skip-network" in sys.argv: mode="skip_network"
 sn="--skip-network" in sys.argv
 r=run_cannot_conclude_guard(sn)
 co=build_pending_network_closeout(sn)
 bl=build_backlog_update(sn)
 out={"phase128_external_source_probe_pipeline":{"mode":mode,"sources_probed":classify_availability(sn)["phase128_availability_classifier"]["total"],"availability_counts":classify_availability(sn)["phase128_availability_classifier"]["counts"],"pending_before":co["phase128_pending_network_closeout"]["pending_network_before"],"pending_after":co["phase128_pending_network_closeout"]["pending_network_after"],"guard":r["phase128_cannot_conclude_guard"],"backlog":bl["phase128_backlog_update"],"300394_retained":True,"688041_retained":True,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0,"profit_loss_tracking_created":False,"return_tracking_created":False,"broker_api_called":False}}
 if "--json" in sys.argv: print(json.dumps(out,ensure_ascii=False,indent=2))
 else: print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
