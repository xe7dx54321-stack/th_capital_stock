import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase132_config import load_config
from smr_phase132_domain_registry import build_domain_registry
from smr_phase132_phase131_coverage_loader import load_phase131_coverage
from smr_phase132_historical_valuation_gap_loader import load_historical_valuation_gap
from smr_phase132_valuation_source_registry import build_valuation_source_registry
from smr_phase132_eastmoney_valuation_adapter import build_eastmoney_valuation_adapter
from smr_phase132_akshare_star_valuation_adapter import build_akshare_star_valuation_adapter
from smr_phase132_third_party_valuation_fallback import build_third_party_valuation_fallback
from smr_phase132_financial_metric_dependency_resolver import build_financial_metric_dependency_resolver
from smr_phase132_ev_ebitda_input_builder import build_ev_ebitda_input
from smr_phase132_ps_ratio_input_builder import build_ps_ratio_input
from smr_phase132_alternative_valuation_metric_builder import build_alternative_valuation_metrics
from smr_phase132_valuation_source_normalizer import build_valuation_source_normalizer
from smr_phase132_valuation_quality_gate import build_valuation_quality_gate
from smr_phase132_valuation_coverage_classifier import classify_valuation_coverage
from smr_phase132_hard_data_valuation_update import build_hard_data_valuation_update
from smr_phase132_watchlist_valuation_update import build_watchlist_valuation_update
from smr_phase132_daily_brief_valuation_update import build_daily_brief_valuation_update
from smr_phase132_signal_effectiveness_valuation_update import build_signal_effectiveness_valuation_update
from smr_phase132_gap_closeout_report import build_gap_closeout_report
from smr_phase132_valuation_integration_board import build_valuation_integration_board
from smr_phase132_valuation_integration_brief import build_valuation_integration_brief_md
from smr_phase132_valuation_memory import build_valuation_memory
from smr_phase132_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase132_backlog_update import build_backlog_update
def main():
 mode="dry_run"
 if "--execute" in sys.argv: mode="execute"
 if "--skip-network" in sys.argv: mode="skip_network"
 gc=build_gap_closeout_report()
 gd=run_cannot_conclude_guard()
 bl=build_backlog_update()
 out={"phase132_valuation_hardening_pipeline":{"mode":mode,"ticker":"688041.SH","valuation_status":gc["phase132_gap_closeout_report"]["overall_resolution"],"all_8_full_coverage":gc["phase132_gap_closeout_report"]["all_8_tickers_now_full_coverage"],"guard":gd["phase132_cannot_conclude_guard"],"backlog":bl["phase132_backlog_update"],"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0,"profit_loss_tracking_created":False,"return_tracking_created":False,"broker_api_called":False}}
 if "--json" in sys.argv: print(json.dumps(out,ensure_ascii=False,indent=2))
 else: print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
