import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_phase97_incremental_loader import load_phase96_existing_db
from smr_phase97_record_fingerprint import dedup_records
from smr_phase97_delta_detector import detect_deltas
from smr_phase97_incremental_writer import write_incremental
from smr_phase97_quality_gate import run_refresh_quality_gate

def build():
    existing=load_phase96_existing_db()
    dedup=dedup_records(existing)
    delta=detect_deltas(existing, existing)
    wr=write_incremental(existing, 'dry-run')
    return run_refresh_quality_gate(dedup, delta, wr)

def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");args=p.parse_args()
    r=build()
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
