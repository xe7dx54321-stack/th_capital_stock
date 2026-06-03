import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase135_phase134_console_loader import load_phase134_console
def main():
 r=load_phase134_console()
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 elif "--markdown" in sys.argv: print(json.dumps(r,ensure_ascii=False))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
