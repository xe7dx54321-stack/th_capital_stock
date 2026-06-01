import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_phase97_config import load_config

def build():
    cfg=load_config()
    return {'phase97_config':{'phase':cfg['phase'],'strategy':cfg['strategy'],'sources':len(cfg['source_refresh_policy']),'dedup_enabled':cfg['dedup']['enabled'],'delta_enabled':cfg['delta']['enabled'],'all_gitignored':cfg['db']['all_gitignored']}}

def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");args=p.parse_args()
    r=build()
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
