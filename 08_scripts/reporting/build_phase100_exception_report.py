import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase100_exception_blocker import build_exception_blocker_report
def main():
    r=build_exception_blocker_report({"phase98_pipeline":{"sources_monitored":7,"alerts_created":0,"quality_gate":"pass"}})
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
