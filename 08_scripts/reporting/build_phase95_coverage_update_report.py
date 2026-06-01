import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase95_300394_resolver import resolve_300394
from smr_phase95_688041_valuation import harden_valuation
from smr_phase95_688041_pricing import harden_pricing
from smr_phase95_coverage_update import build_coverage
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    r3=resolve_300394(mode);v6=harden_valuation(mode);p6=harden_pricing(mode)
    r=build_coverage(r3,v6,p6)
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
