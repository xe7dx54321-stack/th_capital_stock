import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase120_closeout_board import build_closeout_board
def main():
 r=build_closeout_board()
 if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
 else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
