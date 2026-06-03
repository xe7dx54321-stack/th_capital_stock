import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase134_phase133_dashboard_loader import load_phase133_dashboard
from smr_phase134_console_data_aggregator import build_console_data_aggregator
from smr_phase134_console_quality_gate import run_console_quality_gate
from smr_phase134_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase134_backlog_update import build_backlog_update
def main():
 p133=load_phase133_dashboard()
 agg=build_console_data_aggregator()
 gq=run_console_quality_gate()
 cg=run_cannot_conclude_guard()
 bl=build_backlog_update()
 r={"phase134_dashboard":{"phase":"phase134","strategy":"personal_research_console","research_only":True,"personal_research_console_enabled":True,"tickers_covered":8,"markets_covered":3,"phase133_loader":p133["phase134_phase133_dashboard_loader"],"aggregator":agg["phase134_console_data_aggregator"],"quality_gate":gq["phase134_console_quality_gate"],"cannot_conclude_guard":cg["phase134_cannot_conclude_guard"],"backlog":bl["phase134_backlog_update"],"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0,"trade_recommendation_created":0}}
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
