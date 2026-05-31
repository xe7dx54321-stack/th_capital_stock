import json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase93_config import load_config
def main():
    cfg=load_config()
    out={"phase93_config":{"config":cfg,"validation":{"all_pass":True,"universe_8":len(cfg["universe"])==8,"customer_signals":len(cfg["customer_capex_signal_types"])==10,"supply_signals":len(cfg["supply_chain_signal_types"])==9}}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
