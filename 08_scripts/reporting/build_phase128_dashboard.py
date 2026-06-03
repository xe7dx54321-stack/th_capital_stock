import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase128_availability_classifier import classify_availability
from smr_phase128_pending_network_closeout import build_pending_network_closeout
from smr_phase128_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase128_backlog_update import build_backlog_update
from smr_phase128_source_validation_gap_register import build_source_validation_gap_register
def main():
 av=classify_availability()
 co=build_pending_network_closeout()
 gd=run_cannot_conclude_guard()
 bl=build_backlog_update()
 gp=build_source_validation_gap_register()
 r={"phase128_dashboard":{"phase":"phase128","strategy":"external_network_source_probe_and_validation","sources_probed":av["phase128_availability_classifier"]["total"],"availability_counts":av["phase128_availability_classifier"]["counts"],"pending_before":co["phase128_pending_network_closeout"]["pending_network_before"],"pending_after":co["phase128_pending_network_closeout"]["pending_network_after"],"guard":gd["phase128_cannot_conclude_guard"],"backlog":bl["phase128_backlog_update"],"gaps":gp["phase128_source_validation_gap_register"],"300394_retained":True,"688041_retained":True,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0}}
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
