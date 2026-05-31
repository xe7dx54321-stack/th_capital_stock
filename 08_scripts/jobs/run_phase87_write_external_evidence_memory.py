import argparse,json,sys
from pathlib import Path;L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase87_external_evidence import build_external_evidence

def build():return build_memory(dry_run=False)

def build_memory(dry_run=False):
    r=build_external_evidence();rows=r["phase87_external_evidence"]["rows"]
    recs=[]
    for row in rows:
        recs.append({"ticker":row["ticker"],"market":row["market"],"evidence_type":row["evidence_type"],"source_type":"phase87_external","dry_run":dry_run})
    return {"phase87_external_evidence_memory":{"records_written":len(recs) if not dry_run else 0,"records_dry_run":len(recs),"rows":recs,"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}

def main():
    p=argparse.ArgumentParser();p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--json",action="store_true");a=p.parse_args()
    dry=a.dry_run or (not a.execute);r=build_memory(dry_run=dry)
    if a.json:print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
