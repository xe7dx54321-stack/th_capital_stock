import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase123_feedback_memory_writer import build_feedback_memory_writer
def main():
 r=build_feedback_memory_writer()
 if "--json" in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))
 else: print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
