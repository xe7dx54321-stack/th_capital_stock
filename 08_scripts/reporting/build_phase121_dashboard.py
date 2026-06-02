import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase121_config import load_config
from smr_phase121_target_universe import build_target_universe
from smr_phase121_source_candidate_registry import build_source_candidate_registry
from smr_phase121_source_coverage_matrix import build_source_coverage_matrix
from smr_phase121_source_gap_register import build_source_gap_register
from smr_phase121_expansion_board import build_expansion_board
from smr_phase121_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase121_backlog_update import build_backlog_update
def main():
 cfg=load_config()
 uni=build_target_universe()
 scr=build_source_candidate_registry()
 mat=build_source_coverage_matrix()
 grp=build_source_gap_register()
 brd=build_expansion_board()
 grd=run_cannot_conclude_guard()
 blg=build_backlog_update()
 d={"summary":{"phase":"phase121","generated_at":datetime.now().isoformat(),"research_only":True,"source_candidates":scr["phase121_source_candidate_registry"]["total"],"hk_tickers":2,"us_tickers":2,"risk_reduced":mat["phase121_source_coverage_matrix"]["single_source_risk_reduced_count"],"remaining_gaps":mat["phase121_source_coverage_matrix"]["remaining_source_gap_count"],"guard":grd["phase121_guard"]["overall"],"violations":grd["phase121_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":blg["phase121_backlog"]["next_phase"],"paper_order_created":0,"paper_trade_created":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False}}
 if "--json" in sys.argv: print(json.dumps(d,ensure_ascii=False,indent=2))
 else: print(json.dumps(d,ensure_ascii=False))
if __name__=="__main__":main()
