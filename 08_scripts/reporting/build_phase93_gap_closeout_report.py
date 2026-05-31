import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase93_customer_exploration import explore_customer_sources
from smr_phase93_supply_exploration import explore_supply_sources
from smr_phase93_coverage_matrices import build_coverage_matrices
from smr_phase93_gap_closeout import build_gap_closeout
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    ce=explore_customer_sources(mode)
    se=explore_supply_sources(mode)
    cm=build_coverage_matrices(ce,se)
    r=build_gap_closeout(cm)
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
