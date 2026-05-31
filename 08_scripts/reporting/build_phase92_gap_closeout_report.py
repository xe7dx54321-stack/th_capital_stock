import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase92_order_source_exploration import explore_order_sources
from smr_phase92_order_coverage_matrix import build_order_coverage_matrix
from smr_phase92_gap_closeout import build_gap_closeout
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
    exp=explore_order_sources(mode)
    matrix=build_order_coverage_matrix(exp)
    result=build_gap_closeout(matrix,exp)
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
