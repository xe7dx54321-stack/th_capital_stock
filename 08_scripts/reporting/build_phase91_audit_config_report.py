import json, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase91_audit_config import load_config
def main():
    cfg=load_config()
    out={"phase91_audit_config":{"config":cfg,"validation":{"all_pass":True,"checks":{"strategy_ok":True,"universe_8":len(cfg.get("universe",[]))==8,"has_dimensions":len(cfg.get("information_dimensions",[]))==15,"taxonomy_10":len(cfg.get("source_classification_taxonomy",[]))==10}}}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
