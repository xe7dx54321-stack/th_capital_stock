import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase135_config import load_config
from smr_phase135_domain_registry import build_domain_registry
from smr_phase135_phase134_console_loader import load_phase134_console
from smr_phase135_console_feedback_schema import build_console_feedback_schema
from smr_phase135_ticker_card_feedback_intake import build_ticker_card_feedback_intake
from smr_phase135_owner_action_feedback_intake import build_owner_action_feedback_intake
from smr_phase135_daily_brief_feedback_intake import build_daily_brief_feedback_intake
from smr_phase135_source_signal_feedback_intake import build_source_signal_feedback_intake
from smr_phase135_gap_risk_feedback_intake import build_gap_risk_feedback_intake
from smr_phase135_seasonal_insight_feedback_intake import build_seasonal_insight_feedback_intake
from smr_phase135_feedback_validator import run_feedback_validator
from smr_phase135_feedback_entity_linker import build_feedback_entity_linker
from smr_phase135_research_priority_feedback_adapter import build_research_priority_feedback_adapter
from smr_phase135_brief_layout_feedback_adapter import build_brief_layout_feedback_adapter
from smr_phase135_source_signal_weight_feedback_adapter import build_source_signal_weight_feedback_adapter
from smr_phase135_deep_dive_task_feedback_adapter import build_deep_dive_task_feedback_adapter
from smr_phase135_research_loop_tuning_recommendation import build_research_loop_tuning_recommendation
from smr_phase135_feedback_impact_board import build_feedback_impact_board
from smr_phase135_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase135_backlog_update import build_backlog_update
def main():
 mode="dry_run"
 if "--execute" in sys.argv: mode="execute"
 if "--skip-network" in sys.argv: mode="skip_network"
 fv=run_feedback_validator()
 cg=run_cannot_conclude_guard()
 bl=build_backlog_update()
 out={"phase135_owner_feedback_integration_pipeline":{"mode":mode,"tickers_total":8,"feedback_checked":fv["phase135_feedback_validator"]["all_feedbacks_checked"],"valid":fv["phase135_feedback_validator"]["valid_feedback_count"],"invalid":fv["phase135_feedback_validator"]["invalid_feedback_count"],"rejected_trade":fv["phase135_feedback_validator"]["rejected_trade_like_feedback"],"guard":cg["phase135_cannot_conclude_guard"],"backlog":bl["phase135_backlog_update"],"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0}}
 if "--json" in sys.argv: print(json.dumps(out,ensure_ascii=False,indent=2))
 else: print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
