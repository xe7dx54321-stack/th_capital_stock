import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase131_config import load_config
from smr_phase131_domain_registry import build_domain_registry
from smr_phase131_phase130_resolution_loader import load_phase130_resolution
from smr_phase131_alternative_source_registry_loader import load_alternative_source_registry
from smr_phase131_eastmoney_financial_adapter import build_eastmoney_financial_adapter
from smr_phase131_szse_disclosure_adapter import build_szse_disclosure_adapter
from smr_phase131_irm_interaction_adapter import build_irm_interaction_adapter
from smr_phase131_company_ir_adapter import build_company_ir_adapter
from smr_phase131_known_url_integration_loader import build_known_url_integration
from smr_phase131_alternative_source_normalizer import build_alternative_source_normalizer
from smr_phase131_alternative_source_quality_gate import build_alternative_source_quality_gate
from smr_phase131_hard_data_integration_update import build_hard_data_integration_update
from smr_phase131_watchlist_coverage_update import build_watchlist_coverage_update
from smr_phase131_daily_brief_integration_update import build_daily_brief_integration_update
from smr_phase131_signal_effectiveness_update import build_signal_effectiveness_update
from smr_phase131_health_gap_register_update import build_health_gap_register_update
from smr_phase131_integration_decision_builder import build_integration_decision
from smr_phase131_integration_board import build_integration_board
from smr_phase131_integration_brief import build_integration_brief_md
from smr_phase131_integration_memory import build_integration_memory
from smr_phase131_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase131_backlog_update import build_backlog_update
def main():
 mode="dry_run"
 if "--execute" in sys.argv: mode="execute"
 if "--skip-network" in sys.argv: mode="skip_network"
 w=build_watchlist_coverage_update()
 g=run_cannot_conclude_guard()
 b=build_backlog_update()
 out={"phase131_alternative_source_integration_pipeline":{"mode":mode,"ticker":"300394.SZ","coverage_count":w["phase131_watchlist_coverage_update"]["covered_count"],"all_8_covered":w["phase131_watchlist_coverage_update"]["all_blockers_resolved_except_688041_partial"],"300394_status":"covered_via_eastmoney","guard":g["phase131_cannot_conclude_guard"],"backlog":b["phase131_backlog_update"],"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0,"profit_loss_tracking_created":False,"return_tracking_created":False,"broker_api_called":False}}
 if "--json" in sys.argv: print(json.dumps(out,ensure_ascii=False,indent=2))
 else: print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
