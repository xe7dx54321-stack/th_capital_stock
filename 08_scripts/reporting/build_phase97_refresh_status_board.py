import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_phase97_source_refresh_planner import build_refresh_plan
from smr_phase97_delta_detector import detect_deltas
from smr_phase97_record_fingerprint import dedup_records
from smr_phase97_incremental_loader import load_phase96_existing_db
from smr_phase97_refresh_status_board import build_refresh_status_board

def build():
    plan=build_refresh_plan()
    existing=load_phase96_existing_db()
    delta=detect_deltas(existing, existing)
    dedup=dedup_records(existing)
    return build_refresh_status_board(plan, delta, dedup)

def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");args=p.parse_args()
    r=build()
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
