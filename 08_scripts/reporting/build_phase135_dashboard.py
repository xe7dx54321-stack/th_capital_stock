import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase135_phase134_console_loader import load_phase134_console
from smr_phase135_feedback_validator import run_feedback_validator
from smr_phase135_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase135_backlog_update import build_backlog_update
def main():
 p134=load_phase134_console()
 fv=run_feedback_validator()
 cg=run_cannot_conclude_guard()
 bl=build_backlog_update()
 r={"phase135_dashboard":{"phase":"phase135","strategy":"owner_feedback_integration","research_only":True,"owner_feedback_integration_enabled":True,"research_loop_tuning_enabled":True,"phase134_loader":p134["phase135_phase134_console_loader"],"feedback_validator":fv["phase135_feedback_validator"],"guard":cg["phase135_cannot_conclude_guard"],"backlog":bl["phase135_backlog_update"],"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0}}
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
