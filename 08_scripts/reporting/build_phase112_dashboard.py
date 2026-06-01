import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase112_config import load_config
from smr_phase112_opportunity_source_registry import build_opportunity_source_registry
from smr_phase112_opportunity_ranking import build_opportunity_ranking
from smr_phase112_cannot_conclude_guard import run_opportunity_cannot_conclude_guard
from smr_phase112_backlog_update import build_backlog_update
def main():
    cfg=load_config();src=build_opportunity_source_registry();rank=build_opportunity_ranking()
    guard=run_opportunity_cannot_conclude_guard();bl=build_backlog_update()
    summary={"phase":"phase112","research_only":cfg["research_only"],"trade_recommendation_allowed":cfg["trade_recommendation_allowed"],"target_price_output_allowed":cfg["target_price_output_allowed"],"position_sizing_allowed":cfg["position_sizing_allowed"],"paper_execution_enabled":cfg["paper_execution_enabled"],"opportunity_discovery_mode":cfg["opportunity_discovery_mode"],"active_sources":src["phase112_opportunity_source_registry"]["active_sources"],"candidates_ranked":rank["phase112_opportunity_ranking"]["total_ranked"],"guard":guard["phase112_guard"]["overall"],"violations":guard["phase112_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"opportunity_radar_missing":bl["phase112_backlog"]["opportunity_radar_missing"],"next_phase":bl["phase112_backlog"]["next_phase_recommendation"],"paper_order_created":0,"paper_trade_created":0,"target_price_created":0,"position_sizing_created":0,"trade_recommendation_created":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
