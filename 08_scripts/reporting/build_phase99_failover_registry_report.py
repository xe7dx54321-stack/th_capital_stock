import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase99_source_failover_registry import build_failover_registry
def main(): r=build_failover_registry();print(json.dumps(r,ensure_ascii=False,indent=2) if "--json" in sys.argv else json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
