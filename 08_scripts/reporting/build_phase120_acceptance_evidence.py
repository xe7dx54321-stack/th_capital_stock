import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase120_acceptance_evidence import build_acceptance_evidence
def main():
 r=build_acceptance_evidence()
 if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
 else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
