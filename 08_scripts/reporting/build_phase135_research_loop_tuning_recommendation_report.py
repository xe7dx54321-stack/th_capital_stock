import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase135_research_loop_tuning_recommendation import build_research_loop_tuning_recommendation
def main():
 r=build_research_loop_tuning_recommendation()
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 elif "--markdown" in sys.argv: print(json.dumps(r,ensure_ascii=False))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
