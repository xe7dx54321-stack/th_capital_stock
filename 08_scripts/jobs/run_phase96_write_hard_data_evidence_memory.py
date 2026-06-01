import argparse,json,sys,os,uuid
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
MEM_PATH=os.path.join(os.path.dirname(__file__),"..","..","09_runbooks","generated","phase96_hard_data_evidence_memory.jsonl")
def main():
    from smr_phase96_evidence_loader import load_phase92_95_evidence
    p=argparse.ArgumentParser();p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--json",action="store_true")
    args=p.parse_args()
    ev=load_phase92_95_evidence();recs=ev["phase96_evidence_loader"]["records"]
    now=datetime.now().isoformat()
    evidence=[]
    for r in recs:
        evidence.append({"evidence_id":f"phase96-{r['ticker']}-{uuid.uuid4().hex[:8]}","ticker":r["ticker"],"hard_data_category":r["hard_data_category"],"data_type":r.get("data_type",""),"confidence":r.get("confidence","medium"),"limitation":r.get("limitation",""),"cannot_conclude":r.get("cannot_conclude",[]),"created_at":now})
    if args.execute:
        os.makedirs(os.path.dirname(MEM_PATH),exist_ok=True)
        with open(MEM_PATH,"a",encoding="utf-8") as f:
            for e in evidence: f.write(json.dumps(e,ensure_ascii=False)+"\n")
        print(json.dumps({"mode":"execute","records_written":len(evidence),"memory_path_ignored":True},ensure_ascii=False,indent=2))
    else:
        print(json.dumps({"mode":"dry_run","records_would_write":len(evidence),"memory_path_ignored":True},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
