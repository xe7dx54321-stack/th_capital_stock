import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase93_customer_exploration import explore_customer_sources
from smr_phase93_supply_exploration import explore_supply_sources
from smr_phase93_evidence_extraction import extract_evidence
MP="09_runbooks/generated/phase93_evidence_memory.jsonl"
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    ce=explore_customer_sources(mode)
    se=explore_supply_sources(mode)
    ev=extract_evidence(ce,se)
    written=0
    if mode=="execute":
        os.makedirs(os.path.dirname(MP),exist_ok=True)
        with open(MP,"a",encoding="utf-8") as f:
            for rec in ev["phase93_evidence_extraction"]["evidence_records"]:
                for item in rec.get("customer_evidence",[])+rec.get("supply_evidence",[]):
                    f.write(json.dumps({"ts":datetime.now().isoformat(),"phase":"phase93","ticker":rec["ticker"],"evidence":item},ensure_ascii=False)+"\n")
                    written+=1
    out={"phase93_evidence_memory":{"mode":mode,"records_written":written,"memory_path":MP,"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
