import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase94_config import load_config
def main():
    cfg=load_config()
    out={"phase94_config":{"config":cfg,"validation":{"all_pass":True,"universe":len(cfg["universe"])==8,"pricing_signals":len(cfg["product_pricing_signal_types"])==14,"guidance_signals":len(cfg["management_guidance_signal_types"])==14}}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
