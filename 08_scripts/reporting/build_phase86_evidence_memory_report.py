import argparse,json,sys
from pathlib import Path;L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase86_closeout_audit import build_expectation_pricing_closeout
def build():
    r=build_expectation_pricing_closeout();rows=r["phase86_expectation_pricing_closeout"]["rows"]
    records=[]
    for row in rows:
        records.append({"ticker":row["ticker"],"market":row["market"],"pricing_available":row["pricing_available"],"expectation_available":row["expectation_available"],"source_type":"phase86_expectation_pricing","memory_path_ignored":True})
    return {"phase86_evidence_memory":{"records_written":len(records),"rows":records,"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
