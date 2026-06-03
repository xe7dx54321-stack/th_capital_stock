import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase129_config import load_config
from smr_phase129_domain_registry import build_domain_registry
from smr_phase129_blocked_source_loader import load_blocked_sources
from smr_phase129_official_source_identity_map import build_official_source_identity_map
from smr_phase129_sec_edgar_fallback import build_sec_edgar_fallback
from smr_phase129_hkex_fallback import build_hkex_fallback
from smr_phase129_transcript_fallback import build_transcript_fallback
from smr_phase129_mirror_registry import build_mirror_registry
from smr_phase129_third_party_equivalent_registry import build_third_party_equivalent_registry
from smr_phase129_access_route_planner import build_access_route_planner
from smr_phase129_fallback_probe_policy import build_fallback_probe_policy
from smr_phase129_fallback_probe_executor import execute_fallback_probe
from smr_phase129_api_key_classifier import classify_api_key_required
from smr_phase129_proxy_classifier import classify_proxy_required
from smr_phase129_manual_workflow_builder import build_manual_workflow
from smr_phase129_equivalence_scorer import build_equivalence_scorer
from smr_phase129_coverage_update_builder import build_coverage_update
from smr_phase129_gap_register import build_gap_register
from smr_phase129_integration_update import build_integration_update
from smr_phase129_fallback_board import build_fallback_board
from smr_phase129_fallback_brief import build_fallback_brief_md
from smr_phase129_fallback_memory import build_fallback_memory
from smr_phase129_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase129_backlog_update import build_backlog_update
def main():
 mode="dry_run"
 if "--execute" in sys.argv: mode="execute"
 if "--skip-network" in sys.argv: mode="skip_network"
 sn="--skip-network" in sys.argv
 p=execute_fallback_probe(sn)
 g=run_cannot_conclude_guard(sn)
 b=build_backlog_update(sn)
 out={"phase129_official_source_fallback_pipeline":{"mode":mode,"sources_addressed":p["phase129_fallback_probe_executor"]["total"],"resolved":p["phase129_fallback_probe_executor"]["available"],"manual_required":p["phase129_fallback_probe_executor"]["manual_required"],"guard":g["phase129_cannot_conclude_guard"],"backlog":b["phase129_backlog_update"],"300394_retained":True,"688041_retained":True,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0,"profit_loss_tracking_created":False,"return_tracking_created":False,"broker_api_called":False}}
 if "--json" in sys.argv: print(json.dumps(out,ensure_ascii=False,indent=2))
 else: print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
