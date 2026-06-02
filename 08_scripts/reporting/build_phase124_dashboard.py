import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase124_config import load_config
from smr_phase124_taxonomy import build_decision_taxonomy
from smr_phase124_reader import build_journal_reader
from smr_phase124_guard import run_cannot_conclude_guard
from smr_phase124_backlog import build_backlog_update
def main():
 cfg=load_config();tax=build_decision_taxonomy();r=build_journal_reader();grd=run_cannot_conclude_guard();bl=build_backlog_update()
 d={"summary":{"phase":"phase124","generated_at":datetime.now().isoformat(),"research_only":True,"decision_journal_enabled":True,"decision_types":tax["phase124_taxonomy"]["total"],"records_loaded":r["phase124_reader"]["records_loaded"],"guard":grd["phase124_guard"]["overall"],"violations":grd["phase124_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":bl["phase124_backlog"]["next_phase"],"paper_order_created":0,"paper_trade_created":0,"target_price_created":0,"position_sizing_created":0,"broker_api_called":False,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
 if "--json" in sys.argv: print(json.dumps(d,ensure_ascii=False,indent=2))
 else: print(json.dumps(d,ensure_ascii=False))
if __name__=="__main__":main()
