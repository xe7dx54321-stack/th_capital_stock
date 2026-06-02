import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase123_config import load_config
from smr_phase123_feedback_schema import build_feedback_schema
from smr_phase123_feedback_classifier import build_feedback_classifier
from smr_phase123_feedback_memory_reader import build_feedback_memory_reader
from smr_phase123_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase123_backlog_update import build_backlog_update
def main():
 cfg=load_config()
 sch=build_feedback_schema()
 clf=build_feedback_classifier()
 mem=build_feedback_memory_reader()
 grd=run_cannot_conclude_guard()
 blg=build_backlog_update()
 d={"summary":{"phase":"phase123","generated_at":datetime.now().isoformat(),"research_only":True,"owner_feedback_enabled":True,"feedback_memory_enabled":True,"feedback_types":clf["phase123_feedback_classifier"]["feedback_types"],"feedback_records_loaded":mem["phase123_feedback_memory_reader"]["records_loaded"],"guard":grd["phase123_guard"]["overall"],"violations":grd["phase123_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":blg["phase123_backlog"]["next_phase"],"trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,"paper_order_created":0,"paper_trade_created":0,"broker_api_called":False,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
 if "--json" in sys.argv: print(json.dumps(d,ensure_ascii=False,indent=2))
 else: print(json.dumps(d,ensure_ascii=False))
if __name__=="__main__":main()
