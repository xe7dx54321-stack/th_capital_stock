import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
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
def main():
 r={
  "phase134_console_export":{
   "console":"Personal Research Console v1",
   "generated":"2026-06-03","research_only":True,
   "aggregator":build_console_data_aggregator()["phase134_console_data_aggregator"],
   "ticker_cards":build_ticker_cards()["phase134_ticker_card_builder"],
   "market_sections":build_market_sections()["phase134_market_section_builder"],
   "research_priority":build_research_priority()["phase134_research_priority_builder"],
   "seasonal_insight":build_seasonal_insight_center()["phase134_seasonal_insight_center"],
   "watchlist":build_watchlist_status_center()["phase134_watchlist_status_center"],
   "opportunity_catalyst":build_opportunity_catalyst_center()["phase134_opportunity_catalyst_center"],
   "source_signal":build_source_signal_quality_center()["phase134_source_signal_quality_center"],
   "gap_risk":build_gap_risk_center()["phase134_gap_risk_center"],
   "owner_actions":build_owner_action_center()["phase134_owner_action_center"],
   "daily_brief":build_daily_brief_preview()["phase134_daily_brief_preview"],
   "memory_feedback":build_memory_feedback_center()["phase134_memory_feedback_center"],
   "system_health":build_system_health_snapshot()["phase134_system_health_snapshot"],
   "artifact_links":build_artifact_link_index()["phase134_artifact_link_index"],
   "quality_gate":run_console_quality_gate()["phase134_console_quality_gate"],
   "cannot_conclude_guard":run_cannot_conclude_guard()["phase134_cannot_conclude_guard"],
   "mock_used":False,"fixture_used":False
  }
 }
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
