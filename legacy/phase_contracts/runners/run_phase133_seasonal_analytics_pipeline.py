import json,sys,os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "08_scripts" / "lib"))
from smr_phase133_config import load_config
from smr_phase133_domain_registry import build_domain_registry
from smr_phase133_phase132_coverage_loader import load_phase132_coverage
from smr_phase133_seasonal_period_registry import build_seasonal_period_registry
from smr_phase133_ticker_financial_valuation_loader import build_ticker_financial_valuation_loader
from smr_phase133_ticker_seasonal_profile_builder import build_ticker_seasonal_profiles
from smr_phase133_cross_market_comparison_builder import build_cross_market_comparison
from smr_phase133_financial_trend_panel_builder import build_financial_trend_panel
from smr_phase133_valuation_trend_panel_builder import build_valuation_trend_panel
from smr_phase133_opportunity_catalyst_panel_builder import build_opportunity_catalyst_panel
from smr_phase133_watchlist_status_panel_builder import build_watchlist_status_panel
from smr_phase133_source_coverage_panel_builder import build_source_coverage_panel
from smr_phase133_signal_effectiveness_panel_builder import build_signal_effectiveness_panel
from smr_phase133_gap_risk_panel_builder import build_gap_risk_panel
from smr_phase133_owner_action_queue_builder import build_owner_action_queue
from smr_phase133_seasonal_analytics_board import build_seasonal_analytics_board
from smr_phase133_seasonal_analytics_brief import build_seasonal_analytics_brief_md
from smr_phase133_seasonal_dashboard_exporter import build_seasonal_dashboard_export
from smr_phase133_seasonal_memory import build_seasonal_memory
from smr_phase133_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase133_backlog_update import build_backlog_update
def main():
 mode="dry_run"
 if "--execute" in sys.argv: mode="execute"
 if "--skip-network" in sys.argv: mode="skip_network"
 gd=run_cannot_conclude_guard()
 bl=build_backlog_update()
 out={"phase133_seasonal_analytics_pipeline":{"mode":mode,"tickers_total":8,"panels_deployed":9,"guard":gd["phase133_cannot_conclude_guard"],"backlog":bl["phase133_backlog_update"],"first_snapshot":True,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0}}
 if "--json" in sys.argv: print(json.dumps(out,ensure_ascii=False,indent=2))
 else: print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
