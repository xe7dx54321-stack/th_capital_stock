import argparse,json,sys
from pathlib import Path;L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase87_external_evidence import build_external_evidence
def build():
    r=build_external_evidence();rows=r["phase87_external_evidence"]["rows"]
    recs=[]
    for row in rows:
        recs.append({"ticker":row["ticker"],"market":row["market"],"evidence_type":row["evidence_type"],"industry":row.get("industry_direction",""),"source_type":"phase87_external_source","memory_path_ignored":True})
    return {"phase87_evidence_memory":{"records_written":len(recs),"rows":recs,"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
