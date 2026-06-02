import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase125_config import load_config
from smr_phase125_taxonomy import build_taxonomy
from smr_phase125_reader import build_reader
from smr_phase125_guard import run_guard
from smr_phase125_backlog import build_backlog
def main():
 t=build_taxonomy();r=build_reader();g=run_guard();b=build_backlog()
 d={"summary":{"phase":"phase125","generated_at":datetime.now().isoformat(),"research_only":True,"outcome_tracking_enabled":True,"outcome_types":t["phase125_taxonomy"]["total"],"records_loaded":r["phase125_reader"]["records_loaded"],"guard":g["phase125_guard"]["overall"],"violations":g["phase125_guard"]["violations"],"profit_loss_tracking_created":False,"return_tracking_created":False,"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":b["phase125_backlog"]["next_phase"],"paper_order_created":0,"paper_trade_created":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
 if "--json" in sys.argv: print(json.dumps(d,ensure_ascii=False,indent=2))
 else: print(json.dumps(d,ensure_ascii=False))
if __name__=="__main__":main()
