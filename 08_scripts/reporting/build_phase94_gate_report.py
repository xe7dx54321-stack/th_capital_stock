import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase94_pricing_exploration import explore_pricing
from smr_phase94_guidance_exploration import explore_guidance
from smr_phase94_evidence import extract_evidence
from smr_phase94_quality_gate import run_gate
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    pe=explore_pricing(mode);ge=explore_guidance(mode)
    ev=extract_evidence(pe,ge);r=run_gate(ev)
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
