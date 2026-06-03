import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase134_config import load_config
from smr_phase134_domain_registry import build_domain_registry
from smr_phase134_phase133_dashboard_loader import load_phase133_dashboard
from smr_phase134_console_data_aggregator import build_console_data_aggregator
from smr_phase134_ticker_card_builder import build_ticker_cards
from smr_phase134_market_section_builder import build_market_sections
from smr_phase134_research_priority_builder import build_research_priority
from smr_phase134_seasonal_insight_center import build_seasonal_insight_center
from smr_phase134_watchlist_status_center import build_watchlist_status_center
from smr_phase134_opportunity_catalyst_center import build_opportunity_catalyst_center
from smr_phase134_source_signal_quality_center import build_source_signal_quality_center
from smr_phase134_gap_risk_center import build_gap_risk_center
from smr_phase134_owner_action_center import build_owner_action_center
from smr_phase134_daily_brief_preview import build_daily_brief_preview
from smr_phase134_memory_feedback_center import build_memory_feedback_center
from smr_phase134_system_health_snapshot import build_system_health_snapshot
from smr_phase134_artifact_link_index import build_artifact_link_index
from smr_phase134_console_quality_gate import run_console_quality_gate
from smr_phase134_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase134_backlog_update import build_backlog_update
from smr_phase134_console_memory import build_console_memory
def main():
 mode="dry_run"
 if "--execute" in sys.argv: mode="execute"
 if "--skip-network" in sys.argv: mode="skip_network"
 gq=run_console_quality_gate()
 cg=run_cannot_conclude_guard()
 bl=build_backlog_update()
 out={"phase134_personal_research_console_pipeline":{"mode":mode,"tickers_total":8,"markets_covered":3,"console_panels":13,"quality_gate":gq["phase134_console_quality_gate"],"cannot_conclude_guard":cg["phase134_cannot_conclude_guard"],"backlog":bl["phase134_backlog_update"],"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0}}
 if "--json" in sys.argv: print(json.dumps(out,ensure_ascii=False,indent=2))
 else: print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
