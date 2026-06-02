import json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase120_closeout_brief import build_closeout_brief_md
def main():
    md=build_closeout_brief_md()
    if "--markdown" in sys.argv:print(md)
    else:
        out={"phase120_brief":{"generated_at":datetime.now().isoformat(),"research_only":True,"trade_recommendation":0,"target_price":0,"position_sizing":0,"mock_used":False,"fixture_used":False}}
        if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
        else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
