import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase100_quality_gate import run_production_quality_gate
def main():
    r=run_production_quality_gate()
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
