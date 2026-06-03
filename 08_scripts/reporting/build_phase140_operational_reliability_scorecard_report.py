import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase140_operational_reliability_scorecard import build_operational_reliability_scorecard
def main():
 r=build_operational_reliability_scorecard()
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 elif "--markdown" in sys.argv: print(json.dumps(r,ensure_ascii=False))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
