import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase95_300394_resolver import resolve_300394
from smr_phase95_688041_valuation import harden_valuation
from smr_phase95_688041_pricing import harden_pricing
MP="09_runbooks/generated/phase95_evidence_memory.jsonl"
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    r3=resolve_300394(mode);v6=harden_valuation(mode);p6=harden_pricing(mode)
    written=0
    if mode=="execute":
        os.makedirs(os.path.dirname(MP),exist_ok=True)
        with open(MP,"a",encoding="utf-8") as f:
            for d in [r3.get("phase95_300394_resolution",{}),v6.get("phase95_688041_valuation",{}),p6.get("phase95_688041_pricing",{})]:
                f.write(json.dumps({"ts":datetime.now().isoformat(),"phase":"phase95","ticker":d.get("ticker",""),"data":d},ensure_ascii=False)+"\n")
                written+=1
    out={"phase95_memory":{"mode":mode,"written":written,"path":MP,"path_ignored":True,"mock":False,"fixture":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
