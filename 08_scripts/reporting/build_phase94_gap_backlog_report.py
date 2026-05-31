import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase94_pricing_exploration import explore_pricing
from smr_phase94_guidance_exploration import explore_guidance
from smr_phase94_coverage import build_coverage
from smr_phase94_gap_backlog import build_gap_closeout, build_backlog
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    pe=explore_pricing(mode);ge=explore_guidance(mode)
    cm=build_coverage(pe,ge)
    gc=build_gap_closeout(cm);bl=build_backlog()
    out={"gap_closeout":gc,"backlog":bl}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
