import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase129_fallback_probe_executor import execute_fallback_probe
from smr_phase129_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase129_backlog_update import build_backlog_update
from smr_phase129_gap_register import build_gap_register
def main():
 p=execute_fallback_probe()
 g=run_cannot_conclude_guard()
 b=build_backlog_update()
 gp=build_gap_register()
 r={"phase129_dashboard":{"phase":"phase129","strategy":"official_source_access_fallback_and_mirror","sources_addressed":p["phase129_fallback_probe_executor"]["total"],"resolved_via_fallback":p["phase129_fallback_probe_executor"]["available"],"manual_required":p["phase129_fallback_probe_executor"]["manual_required"],"guard":g["phase129_cannot_conclude_guard"],"backlog":b["phase129_backlog_update"],"gaps":gp["phase129_gap_register"],"300394_retained":True,"688041_retained":True,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_output":0,"position_sizing_output":0}}
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
