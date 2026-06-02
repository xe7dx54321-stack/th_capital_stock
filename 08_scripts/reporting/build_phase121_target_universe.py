import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','lib'))
from smr_phase121_target_universe import build_target_universe
def main():
 r=build_target_universe()
 if '--json' in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=='__main__':main()
