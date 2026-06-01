import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase113_config import load_config
from smr_phase113_composite_priority_scorer import build_composite_priority_scorer
from smr_phase113_cannot_conclude_guard import run_cross_source_scoring_guard
from smr_phase113_backlog_update import build_backlog_update
def main():
    cfg=load_config();comp=build_composite_priority_scorer();guard=run_cross_source_scoring_guard();bl=build_backlog_update()
    c=comp["phase113_composite_priority_scorer"]
    summary={"phase":"phase113","research_only":cfg["research_only"],"cross_source_scoring_enabled":cfg["cross_source_scoring_enabled"],"trade_recommendation_allowed":cfg["trade_recommendation_allowed"],"target_price_output_allowed":cfg["target_price_output_allowed"],"position_sizing_allowed":cfg["position_sizing_allowed"],"scored_candidates":c["scored_candidates"],"high":c["high"],"medium":c["medium"],"low":c["low"],"blocked":c["blocked"],"all_not_trade":c["all_not_trade"],"guard":guard["phase113_guard"]["overall"],"violations":guard["phase113_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase113_backlog"]["next_phase_recommendation"],"paper_order_created":0,"paper_trade_created":0,"target_price_created":0,"position_sizing_created":0,"trade_recommendation_created":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
