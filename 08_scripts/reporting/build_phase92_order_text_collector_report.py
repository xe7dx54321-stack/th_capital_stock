import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase92_order_source_exploration import explore_order_sources
from smr_phase92_order_text_collector import collect_order_texts
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    exp=explore_order_sources(mode)
    result=collect_order_texts(exp)
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
