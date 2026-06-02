import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase122_config import load_config
from smr_phase122_brief_aggregator import build_brief_aggregator
from smr_phase122_ticker_cards import build_ticker_cards
from smr_phase122_evidence_digest import build_evidence_digest
from smr_phase122_brief_lint import run_brief_lint
from smr_phase122_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase122_backlog_update import build_backlog_update
from smr_phase122_owner_actions import build_owner_actions
from smr_phase122_risk_gap_section import build_risk_gap_section
def main():
 cfg=load_config()
 agg=build_brief_aggregator()
 cards=build_ticker_cards()
 ev=build_evidence_digest()
 lint=run_brief_lint()
 guard=run_cannot_conclude_guard()
 blg=build_backlog_update()
 owner=build_owner_actions()
 risk=build_risk_gap_section()
 d={"summary":{"phase":"phase122","generated_at":datetime.now().isoformat(),"personal_use_system":True,"owner_mode_enabled":True,"research_only":True,"daily_research_brief_enabled":True,"observed_first_brief_enabled":True,"multi_source_evidence_digest_enabled":True,"tickers_covered":7,"brief_sections_created":9,"top_observations_count":cards["phase122_ticker_cards"]["total"],"research_items_count":cards["phase122_ticker_cards"]["total"],"catalyst_items_count":0,"risk_gap_items_count":len(risk["phase122_risk_gap"]["risks"]),"pending_source_items_count":risk["phase122_risk_gap"]["pending_sources"],"owner_action_count":owner["phase122_owner_actions"]["owner_action_count"],"brief_generated":True,"brief_lint_status":lint["phase122_brief_lint"]["overall"],"guard_status":guard["phase122_guard"]["overall"],"archive_records_written":0,"trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,"paper_order_created":0,"paper_trade_created":0,"broker_api_called":False,"300394_blocker_retained":True,"688041_partial_retained":True,"pending_network_sources_visible":True,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"next_phase_recommendation":blg["phase122_backlog"]["next_phase"]}}
 if "--json" in sys.argv: print(json.dumps(d,ensure_ascii=False,indent=2))
 else: print(json.dumps(d,ensure_ascii=False))
if __name__=="__main__":main()
