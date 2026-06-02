import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase126_taxonomy import build_taxonomy
from smr_phase126_usefulness import build_usefulness
from smr_phase126_noise import build_noise
from smr_phase126_scoring import build_scoring
from smr_phase126_guard import run_guard
from smr_phase126_backlog import build_backlog
def main():
 t=build_taxonomy();u=build_usefulness();n=build_noise();s=build_scoring();g=run_guard();b=build_backlog()
 d={"summary":{"phase":"phase126","generated_at":datetime.now().isoformat(),"research_only":True,"signal_types":t["phase126_taxonomy"]["total"],"usefulness_ratings":5,"noise_levels":5,"scoring_recommendations":s["phase126_scoring"]["recommendations_created"],"trade_actions":s["phase126_scoring"]["trade_actions"],"guard":g["phase126_guard"]["overall"],"violations":g["phase126_guard"]["violations"],"profit_loss_tracking_created":False,"return_tracking_created":False,"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"phase111_126_mainline":"complete","next_phase":b["phase126_backlog"]["next_phase"],"paper_order_created":0,"paper_trade_created":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
 if "--json" in sys.argv: print(json.dumps(d,ensure_ascii=False,indent=2))
 else: print(json.dumps(d,ensure_ascii=False))
if __name__=="__main__":main()
