import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase120_safety_boundary import build_safety_boundary_summary
def main():
 r=build_safety_boundary_summary()
 if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
 else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
