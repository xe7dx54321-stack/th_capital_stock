import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase100_cannot_conclude_guard import run_production_guard
def main():
    r=run_production_guard({"phase100_operator_summary":{"markdown":"production status report"}})
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
