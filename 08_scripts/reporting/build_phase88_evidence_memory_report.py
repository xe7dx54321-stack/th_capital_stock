import argparse,json,sys
from pathlib import Path;L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase88_daily_delta_engine import build_daily_delta
def build():
    r=build_daily_delta();rows=r["phase88_daily_delta"]["rows"]
    recs=[]
    for row in rows:
        recs.append({"ticker":row["ticker"],"market":row["market"],"signal_id":row.get("signal_id",""),"freshness":row.get("freshness",""),"novelty":row.get("novelty",""),"source_type":"phase88_daily_external","memory_path_ignored":True})
    return {"phase88_evidence_memory":{"records_written":len(recs),"rows":recs,"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
def main():p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");a=p.parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
