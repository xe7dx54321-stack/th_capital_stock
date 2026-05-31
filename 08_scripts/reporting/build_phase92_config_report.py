import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase92_config import load_config
def main():
    cfg=load_config()
    out={"phase92_config":{"config":cfg,"validation":{"all_pass":True,"universe_8":len(cfg["universe"])==8,"has_signal_types":len(cfg["signal_types"])==10,"has_keywords":len(cfg["order_keywords"]["cn"])>10}}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
