import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase99_primary_source_retry import run_primary_retry
from smr_phase99_fallback_execution import run_fallback_execution
def main(): retry=run_primary_retry("dry-run");r=run_fallback_execution(retry,"dry-run");print(json.dumps(r,ensure_ascii=False,indent=2) if "--json" in sys.argv else json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
