import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase100_config import load_config
def main():
    c=load_config();out={"phase100_config":{"phase":c["phase"],"pipeline_order":c["production"]["pipeline_order"],"reports_gitignored":c["reports"]["gitignored"],"mock_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
