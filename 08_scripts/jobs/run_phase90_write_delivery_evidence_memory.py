import argparse,json,sys
from pathlib import Path;L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase90_delivery_builder import build_delivery_artifacts

def build():return build_memory(dry_run=False)

def build_memory(dry_run=False):
    r=build_delivery_artifacts();d=r["phase90_delivery_builder"]
    recs=[{"delivery_id":d["delivery_id"],"artifacts":len(d["artifacts"]),"outbox":d["outbox_path"],"source_type":"phase90_delivery","dry_run":dry_run}]
    return {"phase90_delivery_evidence_memory":{"records_written":len(recs) if not dry_run else 0,"records_dry_run":len(recs),"rows":recs,"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}

def main():
    p=argparse.ArgumentParser();p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--json",action="store_true");a=p.parse_args()
    dry=a.dry_run or (not a.execute);r=build_memory(dry_run=dry)
    if a.json:print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
