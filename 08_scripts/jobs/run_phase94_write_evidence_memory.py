import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase94_pricing_exploration import explore_pricing
from smr_phase94_guidance_exploration import explore_guidance
from smr_phase94_evidence import extract_evidence
MP="09_runbooks/generated/phase94_evidence_memory.jsonl"
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    pe=explore_pricing(mode);ge=explore_guidance(mode)
    ev=extract_evidence(pe,ge)
    written=0
    if mode=="execute":
        os.makedirs(os.path.dirname(MP),exist_ok=True)
        with open(MP,"a",encoding="utf-8") as f:
            for rec in ev["phase94_evidence"]["records"]:
                for item in rec.get("pricing_ev",[])+rec.get("guidance_ev",[]):
                    f.write(json.dumps({"ts":datetime.now().isoformat(),"phase":"phase94","ticker":rec["ticker"],"evidence":item},ensure_ascii=False)+"\n")
                    written+=1
    out={"phase94_evidence_memory":{"mode":mode,"written":written,"path":MP,"path_ignored":True,"mock":False,"fixture":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
