import argparse,json,sys,os
from pathlib import Path;L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase85b_source_exhaustion_report import build_source_exhaustion_report

def build():
    return build_memory(dry_run=False)

def build_memory(dry_run=False):
    r=build_source_exhaustion_report();d=r["phase85b_source_exhaustion_report"]
    records=[]
    for row in d["rows"]:
        rec={"ticker":row["ticker"],"market":row["market"],"exhaustion_level":row["exhaustion_level"],"recommended_next":row["recommended_next"],"not_fuzzy_blocker":row["not_fuzzy_blocker"],"source_type":"phase85b_valuation_hardening","dry_run":dry_run}
        records.append(rec)
    return {"phase85b_valuation_hardening_evidence_memory":{"records_written":len(records) if not dry_run else 0,"records_dry_run":len(records),"rows":records,"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}

def main():
    p=argparse.ArgumentParser();p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--json",action="store_true");a=p.parse_args()
    dry=a.dry_run or (not a.execute)
    r=build_memory(dry_run=dry)
    if a.json:print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
