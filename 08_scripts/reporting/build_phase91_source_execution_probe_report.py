import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase91_source_inventory import build_source_inventory
from smr_phase91_source_execution_probe import run_probes
def main():
    inv=build_source_inventory()
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    result=run_probes(inv,mode)
    if "--json" in sys.argv:print(json.dumps(result,ensure_ascii=False,indent=2))
    else:print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
