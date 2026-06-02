import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase114_config import load_config
from smr_phase114_catalyst_confidence_scorer import build_catalyst_confidence_scorer
from smr_phase114_cannot_conclude_guard import run_catalyst_guard
from smr_phase114_backlog_update import build_backlog_update
def main():
    cfg=load_config();conf=build_catalyst_confidence_scorer();guard=run_catalyst_guard();bl=build_backlog_update()
    summary={"phase":"phase114","research_only":cfg["research_only"],"catalyst_detection_enabled":cfg["catalyst_detection_enabled"],"trade_recommendation_allowed":cfg["trade_recommendation_allowed"],"target_price_output_allowed":cfg["target_price_output_allowed"],"high_confidence":conf["phase114_catalyst_confidence_scorer"]["high_confidence"],"guard":guard["phase114_guard"]["overall"],"violations":guard["phase114_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase114_backlog"]["next_phase_recommendation"],"paper_order_created":0,"paper_trade_created":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
