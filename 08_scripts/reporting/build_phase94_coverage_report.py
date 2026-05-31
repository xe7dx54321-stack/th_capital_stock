import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase94_pricing_exploration import explore_pricing
from smr_phase94_guidance_exploration import explore_guidance
from smr_phase94_coverage import build_coverage
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    pe=explore_pricing(mode);ge=explore_guidance(mode)
    r=build_coverage(pe,ge)
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
